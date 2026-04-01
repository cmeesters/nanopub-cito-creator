import wx
from models.citation_types import CITATION_TYPES, CONFLICTING_COMBINATIONS, get_citation_sentiment
from ui.conflict_dialog import ConflictDialog

# Custom return codes for dialog
DIALOG_BACK = 100

class CitationDialog(wx.Dialog):
    def __init__(self, parent, doi, title, authors=None, citation_number=None, pre_selected=None):
        super().__init__(parent, title="Select CiTO Types", size=(900, 700), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.doi = doi
        self.title = title
        self.authors = authors if authors else ""
        self.citation_number = citation_number
        self.pre_selected = pre_selected if pre_selected else []
        self.checkboxes = {}
        self._build()

    def _build(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        bold_font = wx.Font(wx.FontInfo(12).Bold())
        italic_font = wx.Font(wx.FontInfo(12).Italic())

        # Citation number header (if provided)
        if self.citation_number is not None:
            num_lbl = wx.StaticText(self, label=f"No. {self.citation_number}")
            num_lbl.SetFont(bold_font)
            vbox.Add(num_lbl, 0, wx.ALL, 8)

        # DOI Header
        doi_lbl = wx.StaticText(self, label=f"Cited DOI: {self.doi}")
        doi_lbl.SetFont(bold_font)
        vbox.Add(doi_lbl, 0, wx.ALL, 8)

        # Title with bold "Title:" label
        title_box = wx.BoxSizer(wx.HORIZONTAL)
        title_label = wx.StaticText(self, label="Title: ")
        title_label.SetFont(bold_font)
        title_text = wx.StaticText(self, label=f'"{self.title}"')
        title_text.SetFont(italic_font)
        title_text.Wrap(680)
        title_box.Add(title_label, 0)
        title_box.Add(title_text, 1, wx.EXPAND)
        vbox.Add(title_box, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # Authors (only show if we have them)
        if self.authors:
            authors_lbl = wx.StaticText(self, label=f"First Author: {self.authors}")
            vbox.Add(authors_lbl, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # Horizontal line
        line = wx.StaticLine(self, style=wx.LI_HORIZONTAL)
        vbox.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # Instruction
        vbox.Add(wx.StaticText(self, label="Select CiTO citation types:"), 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # Scrolled panel for checkboxes
        scrolled = wx.ScrolledWindow(self, style=wx.VSCROLL)
        scrolled.SetScrollRate(0, 20)
        scrolled.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_DEFAULT)
        
        # Calculate number of rows needed for all items in 3 columns
        num_items = len(CITATION_TYPES)
        num_cols = 3
        num_rows = (num_items + num_cols - 1) // num_cols  # Ceiling division
         
        # Grid of checkboxes (3 columns, all rows visible)
        grid_sizer = wx.FlexGridSizer(rows=num_rows, cols=num_cols, hgap=10, vgap=8)
        
        # Add all checkboxes
        for label in CITATION_TYPES.keys():
            cb = wx.CheckBox(scrolled, label=label)
            cb.SetFont(wx.Font(wx.FontInfo(14)))
             
            # Pre-check if this was previously selected
            if label in self.pre_selected:
                cb.SetValue(True)
            
            # Style based on sentiment
            sentiment = get_citation_sentiment(label)
            if sentiment == "positive":
                cb.SetForegroundColour(wx.Colour(0, 100, 0))  # Dark green
            elif sentiment == "negative":
                cb.SetForegroundColour(wx.Colour(178, 34, 34))  # Brick red
            else:
                cb.SetForegroundColour(wx.Colour(0, 0, 0))  # Black
            
            self.checkboxes[label] = cb
            grid_sizer.Add(cb, 0, wx.EXPAND)
        
        # Make columns expandable
        for i in range(num_cols):
            grid_sizer.AddGrowableCol(i)
        scrolled.SetSizer(grid_sizer)
        
        # Buttons - custom layout to position back button on the left
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        back_btn = wx.Button(self, DIALOG_BACK, "\u2190 Back")  # Unicode left arrow
        ok_btn = wx.Button(self, wx.ID_OK)
        cancel_btn = wx.Button(self, wx.ID_CANCEL)
        
        btn_sizer.Add(back_btn, 0, wx.ALL, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)

        vbox.Add(scrolled, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        vbox.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 8)
        self.SetSizer(vbox)

    def on_ok(self, evt):
        selected = self.get_selected_types()
        if self._has_conflicts(selected):
            dlg = ConflictDialog(self, selected)
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
            dlg.Destroy()
        evt.Skip()

    def on_back(self, evt):
        self.EndModal(DIALOG_BACK)

    def get_selected_types(self):
        selected = []
        for label, cb in self.checkboxes.items():
            if cb.GetValue():
                selected.append(label)
        return selected

    def _has_conflicts(self, selected):
        for a, b in CONFLICTING_COMBINATIONS:
            if a in selected and b in selected:
                return True
        return False