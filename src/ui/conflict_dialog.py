import wx
from models.citation_types import CONFLICTING_COMBINATIONS


class ConflictDialog(wx.Dialog):
    def __init__(self, parent, selected_keys):
        super().__init__(parent, title="Conflicting Citation Types")
        self.selected_keys = selected_keys
        self._build()

    def _build(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Header message
        header = wx.StaticText(self, label="You have selected potentially conflicting citation types:")
        header.SetFont(wx.Font(wx.FontInfo(12)))
        vbox.Add(header, 0, wx.ALL, 10)

        # Find and display conflicting pairs
        bold_font = wx.Font(wx.FontInfo(12).Bold())
        normal_font = wx.Font(wx.FontInfo(12))

        for a, b in CONFLICTING_COMBINATIONS:
            if a in self.selected_keys and b in self.selected_keys:
                conflict_box = wx.BoxSizer(wx.HORIZONTAL)
                text_a = wx.StaticText(self, label=a)
                text_a.SetFont(bold_font)
                text_vs = wx.StaticText(self, label=" vs. ")
                text_vs.SetFont(normal_font)
                text_b = wx.StaticText(self, label=b)
                text_b.SetFont(bold_font)
                conflict_box.Add(text_a, 0)
                conflict_box.Add(text_vs, 0)
                conflict_box.Add(text_b, 0)
                vbox.Add(conflict_box, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        vbox.AddSpacer(10)

        # Footer message
        footer = wx.StaticText(self, label="Proceed anyway?")
        footer.SetFont(wx.Font(wx.FontInfo(12)))
        vbox.Add(footer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Buttons
        btn_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        self.SetSizer(vbox)

        self.Fit()