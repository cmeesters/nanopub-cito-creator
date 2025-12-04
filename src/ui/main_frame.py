import wx
import logging
from nanopub import NanopubConf, load_profile
from services.crossref_service import get_cited_papers
from services.nanopub_service import create_nanopub
from ui.citation_dialog import CitationDialog

class MainFrame(wx.Frame):
    def __init__(self, parent, app_state):
        super().__init__(parent, title="CiTO Creator", size=(900, 650))
        self.app_state = app_state
        self._setup_logging()
        self._init_ui()
        self.Centre()
        
        # If initial DOI provided via CLI, populate it
        if self.app_state.initial_doi:
            self.doi_input.SetValue(self.app_state.initial_doi)

    def _setup_logging(self):
        logging.basicConfig(
            filename="create_nanopub.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def _init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        top_box = wx.BoxSizer(wx.HORIZONTAL)
        doi_label = wx.StaticText(panel, label="Original DOI:")
        self.doi_input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.doi_input.Bind(wx.EVT_TEXT_ENTER, self.on_process_doi)
        top_box.Add(doi_label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        top_box.Add(self.doi_input, 1, wx.EXPAND)

        # Options box
        options_box = wx.BoxSizer(wx.HORIZONTAL)
        self.test_server_cb = wx.CheckBox(panel, label="Use test server")
        self.test_server_cb.SetValue(self.app_state.use_test_server)
        self.test_server_cb.Bind(wx.EVT_CHECKBOX, self.on_test_server_toggle)
        
        self.auto_publish_cb = wx.CheckBox(panel, label="Auto-publish")
        self.auto_publish_cb.SetValue(self.app_state.auto_publish)
        self.auto_publish_cb.Bind(wx.EVT_CHECKBOX, self.on_auto_publish_toggle)
        
        options_box.Add(self.test_server_cb, 0, wx.RIGHT, 15)
        options_box.Add(self.auto_publish_cb, 0)

        self.process_btn = wx.Button(panel, label="Process DOI")
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_process_doi)

        self.status = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )

        vbox.Add(top_box, 0, wx.EXPAND | wx.ALL, 10)
        vbox.Add(options_box, 0, wx.LEFT | wx.BOTTOM, 10)
        vbox.Add(self.process_btn, 0, wx.LEFT | wx.BOTTOM, 10)
        vbox.Add(self.status, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(vbox)
        self._build_menu()

    def _build_menu(self):
        menubar = wx.MenuBar()
        
        file_menu = wx.Menu()
        quit_item = file_menu.Append(wx.ID_EXIT, "Quit\tCtrl+Q")
        
        self.Bind(wx.EVT_MENU, self.on_quit, quit_item)
        
        menubar.Append(file_menu, "File")
        self.SetMenuBar(menubar)

    def on_test_server_toggle(self, evt):
        self.app_state.use_test_server = evt.IsChecked()
        
    def on_auto_publish_toggle(self, evt):
        self.app_state.auto_publish = evt.IsChecked()

    def on_process_doi(self, evt):
        doi = self.doi_input.GetValue().strip()
        if not doi:
            wx.MessageBox("Enter a DOI.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        self.app_state.reset()
        self.app_state.set_doi(doi)
         
        self._log(f"Processing DOI: {doi}")
         
        wx.BeginBusyCursor()
        try:
            cited = get_cited_papers(doi)
        finally:
            wx.EndBusyCursor()

        if not cited:
            self._log("No cited papers found.")
            wx.MessageBox("No cited papers found.", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        self._log("─" * 80)
        self.app_state.set_cited_papers(cited)
        self._log(f"Found {len(cited)} cited papers.")
        
        for cited_doi, paper_info in cited.items():
            # Extract title and authors from the dictionary
            title = paper_info['title']
            authors = paper_info['authors']
            
            dlg = CitationDialog(self, cited_doi, title, authors)
            if dlg.ShowModal() == wx.ID_OK:
                selected = dlg.get_selected_types()
                if selected:
                    self.app_state.add_citation(cited_doi, selected)
                    self._log("─" * 80)
                    self._log(f"{cited_doi}: {selected}")
            else:
                # User cancelled - ask if they want to stop processing
                if len(self.app_state.get_citations()) > 0:
                    result = wx.MessageBox(
                        "Stop processing remaining papers?",
                        "Confirm",
                        wx.YES_NO | wx.ICON_QUESTION
                    )
                    dlg.Destroy()
                    if result == wx.YES:
                        break
                else:
                    dlg.Destroy()
                    break
            dlg.Destroy()

        citations = self.app_state.get_citations()
        if not citations:
            self._log("No selections. Aborting nanopub creation.")
            return

        # Confirm publication if not auto-publish
        if not self.app_state.auto_publish:
            msg = f"Create nanopub with {len(citations)} citation(s)?"
            if wx.MessageBox(msg, "Confirm Publication", wx.YES_NO | wx.ICON_QUESTION) != wx.YES:
                self._log("Publication cancelled by user.")
                return

        self._log("Creating nanopub...")
        conf = NanopubConf(
            use_test_server=self.app_state.use_test_server,
            profile=load_profile(),
            add_prov_generated_time=True,
            attribute_publication_to_profile=True,
        )
        try:
            uri = create_nanopub(doi, citations, conf)
            self._log(f"Nanopub URI: {uri}")
            wx.MessageBox(f"Nanopub published:\n{uri}", "Success", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            self._log(f"Error: {e}")
            logging.exception("Nanopub creation failed")
            wx.MessageBox(f"Failed: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _log(self, msg):
        logging.info(msg)
        self.status.AppendText(msg + "\n")

    def on_quit(self, evt):
        self.Close()