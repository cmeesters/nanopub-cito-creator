import wx
import logging
from nanopub import NanopubConf, load_profile
from services.crossref_service import get_cited_papers
from services.nanopub_service import create_nanopub
from ui.citation_dialog import CitationDialog, DIALOG_BACK
from ui.database_helper import DatabaseUIHelper

class MainFrame(wx.Frame):
    def __init__(self, parent, app_state):
        super().__init__(parent, title="CiTO Creator", size=(900, 650))
        self.app_state = app_state
        self.db_helper = DatabaseUIHelper()
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
        self.doi_input.Bind(wx.EVT_TEXT, self.on_doi_changed)
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
        
        self.skip_annotated_cb = wx.CheckBox(panel, label="Skip already annotated")
        self.skip_annotated_cb.SetValue(True)
        
        options_box.Add(self.test_server_cb, 0, wx.RIGHT, 15)
        options_box.Add(self.auto_publish_cb, 0, wx.RIGHT, 15)
        options_box.Add(self.skip_annotated_cb, 0)

        # Buttons box (Process DOI and Publish side by side)
        buttons_box = wx.BoxSizer(wx.HORIZONTAL)
        self.process_btn = wx.Button(panel, label="Process DOI")
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_process_doi)
        
        self.publish_btn = wx.Button(panel, label="Publish Nanopub CiTO")
        self.publish_btn.Bind(wx.EVT_BUTTON, self.on_publish_nanopub)
        self.publish_btn.Enable(False)  # Initially disabled
        
        buttons_box.Add(self.process_btn, 0, wx.RIGHT, 10)
        buttons_box.Add(self.publish_btn, 0)

        self.status = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )

        vbox.Add(top_box, 0, wx.EXPAND | wx.ALL, 10)
        vbox.Add(options_box, 0, wx.LEFT | wx.BOTTOM, 10)
        vbox.Add(buttons_box, 0, wx.LEFT | wx.BOTTOM, 10)
        vbox.Add(self.status, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(vbox)
        self._build_menu()

    def _build_menu(self):
        menubar = wx.MenuBar()
        
        file_menu = wx.Menu()
        quit_item = file_menu.Append(wx.ID_EXIT, "Quit\tCtrl+Q")
        
        self.Bind(wx.EVT_MENU, self.on_quit, quit_item)
        
        # Edit menu with database operations
        edit_menu = wx.Menu()
        self.redo_item = edit_menu.Append(wx.ID_ANY, "Redo Annotation\tCtrl+R", 
                                          "Re-annotate a saved ontology")
        self.continue_item = edit_menu.Append(wx.ID_ANY, "Continue Annotating\tCtrl+L",
                                              "Continue annotating a saved ontology")
        
        self.Bind(wx.EVT_MENU, self.on_redo_annotation, self.redo_item)
        self.Bind(wx.EVT_MENU, self.on_continue_annotating, self.continue_item)
        
        menubar.Append(file_menu, "File")
        menubar.Append(edit_menu, "Edit")
        self.SetMenuBar(menubar)
        
        # Initially disable these buttons
        self._update_database_button_states()

    def on_test_server_toggle(self, evt):
        self.app_state.use_test_server = evt.IsChecked()
        
    def on_auto_publish_toggle(self, evt):
        self.app_state.auto_publish = evt.IsChecked()

    def _update_database_button_states(self):
        """Update the enabled/disabled state of database buttons based on current DOI."""
        doi = self.doi_input.GetValue().strip()
        doi_exists = bool(doi and self.db_helper.check_doi_in_database(doi))
        self.redo_item.Enable(doi_exists)
        self.continue_item.Enable(doi_exists)
        
        # Enable publish button if we have completed annotations
        has_citations = len(self.app_state.get_citations()) > 0
        self.publish_btn.Enable(has_citations)

    def on_doi_changed(self, evt):
        """Handle DOI input change to update button states."""
        self._update_database_button_states()

    def on_redo_annotation(self, evt):
        """Load a saved ontology and start fresh annotation."""
        doi = self.doi_input.GetValue().strip()
        if not doi:
            wx.MessageBox("Enter a DOI.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        if not self.db_helper.check_doi_in_database(doi):
            wx.MessageBox(f"No saved ontology found for DOI: {doi}", "Not Found", 
                         wx.OK | wx.ICON_INFORMATION)
            return
        
        self.app_state.reset()
        if not self.db_helper.load_ontology_for_redo(doi, self.app_state):
            wx.MessageBox(f"Failed to load ontology for DOI: {doi}", "Error", 
                         wx.OK | wx.ICON_ERROR)
            return
        
        self._log(f"Loaded saved ontology for redo: {doi}")
        self._log(f"Previous citations: {self.app_state.get_citations()}")
        
        # Clear previous citations to allow fresh annotation
        self.app_state.clear_citations()
        self._log("Cleared previous citations. Ready for fresh annotation.")

    def on_continue_annotating(self, evt):
        """Continue annotating from a saved ontology."""
        doi = self.doi_input.GetValue().strip()
        if not doi:
            wx.MessageBox("Enter a DOI.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        if not self.db_helper.check_doi_in_database(doi):
            wx.MessageBox(f"No saved ontology found for DOI: {doi}", "Not Found", 
                         wx.OK | wx.ICON_INFORMATION)
            return
        
        self.app_state.reset()
        if not self.db_helper.load_ontology_for_continuation(doi, self.app_state):
            wx.MessageBox(f"Failed to load ontology for DOI: {doi}", "Error", 
                         wx.OK | wx.ICON_ERROR)
            return
        
        self._log(f"Loaded saved ontology for continuation: {doi}")
        self._log(f"Existing citations: {self.app_state.get_citations()}")
        self._log("You can now add more citations or modify existing ones.")

    def on_publish_nanopub(self, evt):
        """Publish nanopub from saved annotations."""
        doi = self.doi_input.GetValue().strip()
        if not doi:
            wx.MessageBox("Enter a DOI.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        citations = self.app_state.get_citations()
        if not citations:
            wx.MessageBox("No citations to publish. Process the DOI first.", "Error", 
                         wx.OK | wx.ICON_ERROR)
            return
        
        # Check if a real nanopub has already been published
        if not self.app_state.use_test_server and self.db_helper.has_real_publication(doi):
            msg = ("A real (non-test) nanopub has already been published for this DOI.\n\n"
                   "Publishing again will create a duplicate nanopub.\n\n"
                   "Are you sure you want to continue?")
            result = wx.MessageBox(msg, "Already Published", 
                                  wx.YES_NO | wx.ICON_WARNING)
            if result != wx.YES:
                return
        
        self._log("Creating nanopub...")
        self._log(f"Test server mode: {self.app_state.use_test_server}")
        self._log(f"Number of citations to publish: {len(citations)}")
        conf = NanopubConf(
            use_test_server=self.app_state.use_test_server,
            profile=load_profile(),
            add_prov_generated_time=True,
            attribute_publication_to_profile=True,
        )
        try:
            uri = create_nanopub(doi, citations, conf)
            self._log(f"Nanopub URI: {uri}")
            self._log("Check create_nanopub.log for detailed RDF graph")
            
            # Save the ontology to database with publication info
            if not self.app_state.use_test_server:
                self.db_helper.mark_real_publication(doi, uri)
                self._log("Marked as published (real nanopub) in database")
            else:
                self.db_helper.save_ontology_state(doi, citations, status="published")
                self._log("Ontology saved to database with status: published (test server)")
            
            self._update_database_button_states()
            
            wx.MessageBox(f"Nanopub published:\n{uri}", "Success", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            self._log(f"Error: {e}")
            logging.exception("Nanopub creation failed")
            wx.MessageBox(f"Failed to publish nanopub:\n{e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_process_doi(self, evt):
        doi = self.doi_input.GetValue().strip()
        if not doi:
            wx.MessageBox("Enter a DOI.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Check if this DOI already has saved data
        if self.db_helper.check_doi_in_database(doi):
            msg = "Found existing annotations for this DOI.\n\nWhat would you like to do?"
            dlg = wx.MessageDialog(
                self, msg, "Resume Annotation?",
                wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
            )
            dlg.SetYesNoCancelLabels("Continue", "Start Fresh", "Cancel")
            result = dlg.ShowModal()
            dlg.Destroy()
            
            if result == wx.ID_YES:
                # Continue from saved state
                self.app_state.reset()
                if self.db_helper.load_ontology_for_continuation(doi, self.app_state):
                    self._log(f"Loaded existing annotations for: {doi}")
                    self._log(f"Previously annotated: {len(self.app_state.get_citations())} citations")
                    # Don't return - continue processing to add more citations
                else:
                    wx.MessageBox("Failed to load saved data.", "Error", wx.OK | wx.ICON_ERROR)
                    return
            elif result == wx.ID_NO:
                # Start fresh - clear existing data
                self.app_state.reset()
                self.app_state.clear_citations()
                self._log(f"Starting fresh annotation for: {doi}")
            else:
                # Cancel
                return
        else:
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
        
        # Get already annotated citations
        already_annotated = set(self.app_state.get_citations().keys())
        if already_annotated:
            self._log(f"Found {len(already_annotated)} already annotated citations.")
        
        # Create ordered list of citations based on skip preference
        skip_annotated = self.skip_annotated_cb.IsChecked()
        if skip_annotated:
            # Only process unannotated citations
            citations_to_process = [(doi, info) for doi, info in cited.items() 
                                   if doi not in already_annotated]
            self._log(f"Skipping already annotated. Processing {len(citations_to_process)} new citations.")
            start_index = 0
        else:
            # Process all citations
            citations_to_process = [(doi, info) for doi, info in cited.items()]
            
            # Find the first unannotated citation to start from
            start_index = 0
            for i, (doi, info) in enumerate(citations_to_process):
                if doi not in already_annotated:
                    start_index = i
                    break
            
            self._log(f"Starting from citation {start_index + 1} (first unannotated citation)")
        
        # Track which citation we're on
        current_index = start_index
        
        while current_index < len(citations_to_process):
            cited_doi, paper_info = citations_to_process[current_index]
            citation_number = current_index + 1  # Overall position in all citations
            
            # Extract title and authors from the dictionary
            title = paper_info['title']
            authors = paper_info['authors']
            
            # Get pre-selected items if this citation was already annotated
            pre_selected = []
            current_citations = self.app_state.get_citations()
            self._log(f"Debug: current_citations keys = {list(current_citations.keys())}")
            if cited_doi in current_citations:
                pre_selected = current_citations[cited_doi]
                self._log(f"Debug: Found pre_selected for {cited_doi}: {pre_selected}")
            else:
                self._log(f"Debug: {cited_doi} NOT in current_citations. This will be a NEW annotation.")
            
            dlg = CitationDialog(self, cited_doi, title, authors, citation_number=citation_number, pre_selected=pre_selected)
            result = dlg.ShowModal()
            dlg.Destroy()
            
            if result == wx.ID_OK:
                selected = dlg.get_selected_types()
                if selected:
                    self.app_state.add_citation(cited_doi, selected)
                    self._log("─" * 80)
                    self._log(f"{cited_doi}: {selected}")
                    
                    # Save progress immediately after each citation
                    self.db_helper.save_ontology_state(doi, self.app_state.get_citations(), status="in_progress")
                    self._log("Progress saved.")
                    self._update_database_button_states()
                # Move to next citation
                current_index += 1
            elif result == DIALOG_BACK:
                # Go back to previous citation
                if current_index > 0:
                    current_index -= 1
                    current_doi = citations_to_process[current_index][0]
                    self._log(f"Going back to No. {current_index + 1}")
                    # Loop will continue with the previous citation
                else:
                    self._log("Already at the first citation.")
            else:
                # User cancelled - ask if they want to stop processing
                if len(self.app_state.get_citations()) > 0:
                    result = wx.MessageBox(
                        "Stop processing remaining papers?",
                        "Confirm",
                        wx.YES_NO | wx.ICON_QUESTION
                    )
                    if result == wx.YES:
                        break
                else:
                    break

        citations = self.app_state.get_citations()
        if not citations:
            self._log("No selections. Aborting nanopub creation.")
            return

        # Save final state and show publish button
        self.db_helper.save_ontology_state(doi, citations, status="completed")
        self._log(f"Annotation complete with {len(citations)} citation(s).")
        self._log("Click 'Publish Nanopub CiTO' button to publish.")
        self._update_database_button_states()
        
        # Auto-publish if enabled
        if self.app_state.auto_publish:
            self.on_publish_nanopub(None)

    def _log(self, msg):
        logging.info(msg)
        self.status.AppendText(msg + "\n")

    def on_quit(self, evt):
        self.Close()