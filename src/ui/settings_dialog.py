import wx

class SettingsDialog(wx.Dialog):
    """Dialog for application settings."""

    def __init__(self, parent, app_state):
        super().__init__(parent, title="Settings", size=(420, 240))
        self.app_state = app_state
        self._build()

    def _build(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        np_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Nanopub Settings")

        self.test_server_cb = wx.CheckBox(panel, label="Use test server")
        self.test_server_cb.SetValue(self.app_state.use_test_server)

        self.auto_publish_cb = wx.CheckBox(panel, label="Auto-publish without confirmation")
        self.auto_publish_cb.SetValue(self.app_state.auto_publish)

        np_box.Add(self.test_server_cb, 0, wx.ALL, 6)
        np_box.Add(self.auto_publish_cb, 0, wx.ALL, 6)

        btn_sizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(panel, wx.ID_OK)
        cancel_btn = wx.Button(panel, wx.ID_CANCEL)
        btn_sizer.AddButton(ok_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()

        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        vbox.Add(np_box, 0, wx.ALL | wx.EXPAND, 10)
        vbox.AddStretchSpacer()
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        panel.SetSizer(vbox)

    def on_ok(self, evt):
        self.app_state.use_test_server = self.test_server_cb.GetValue()
        self.app_state.auto_publish = self.auto_publish_cb.GetValue()
        evt.Skip()