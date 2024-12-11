import pcbnew
import wx
import os

class AddSuffixToSelectedComponentNetsPlugin(pcbnew.ActionPlugin):
    def __init__(self):
        self.name = "Add Suffix or Prefix to Nets of Selected Components"
        self.category = "Modify"
        self.description = "Add a suffix or prefix to nets associated with selected components in the PCB layout"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "Net_Suffix.png")

    def Run(self):
        # Access the PCB board
        board = pcbnew.GetBoard()
        if not board:
            wx.MessageBox("No PCB layout is open. Please open a PCB layout.",
                          "Error", wx.OK | wx.ICON_ERROR)
            return

        # Detect selected components
        selected_components = self.get_selected_components(board)
        if not selected_components:
            wx.MessageBox("No components are selected. Please select components on the PCB and try again.",
                          "Warning", wx.OK | wx.ICON_WARNING)
            return

        # Get nets associated with the selected components, excluding unconnected pads
        nets = self.get_nets_from_components(selected_components)
        if not nets:
            wx.MessageBox("No nets found for the selected components.",
                          "Warning", wx.OK | wx.ICON_WARNING)
            return

        # Ask the user to select nets from the list, sorted alphabetically
        net_names = sorted(nets.keys())  # Sort net names alphabetically
        selected_net_names = self.ask_user_net_selection(net_names)
        if not selected_net_names:
            wx.MessageBox("No nets selected. Exiting...",
                          "Info", wx.OK | wx.ICON_INFORMATION)
            return

        # Ask user for suffix or prefix and mode
        suffix_or_prefix, mode = self.ask_user_suffix_or_prefix()
        if not suffix_or_prefix:
            wx.MessageBox("No suffix or prefix entered. Exiting...",
                          "Info", wx.OK | wx.ICON_INFORMATION)
            return

        # Update only the selected nets
        for net_name in selected_net_names:
            net = nets[net_name]  # Get the exact net object
            base_name = self.strip_existing_suffix_or_prefix(net.GetNetname(), mode)
            if mode == "suffix":
                new_name = f"{base_name}_{suffix_or_prefix}"
            else:  # mode == "prefix"
                new_name = f"{suffix_or_prefix}_{base_name}"
            print(f"Updating net: {net.GetNetname()} -> {new_name}")
            net.SetNetname(new_name)

        # Refresh the PCB layout view
        pcbnew.Refresh()
        wx.MessageBox(f"Updated nets: {', '.join(selected_net_names)}",
                      "Success", wx.OK | wx.ICON_INFORMATION)

    def get_selected_components(self, board):
        # Retrieve all selected components on the PCB using IsSelected
        selected_components = [
            item for item in board.GetFootprints() if item.IsSelected()
        ]
        print(f"Selected components found: {len(selected_components)}")
        return selected_components

    def get_nets_from_components(self, components):
        # Extract nets connected to the selected components, excluding unconnected or placeholder nets
        nets = {}
        for component in components:
            for pad in component.Pads():
                net = pad.GetNet()
                if net and net.GetNetname() and not net.GetNetname().lower().startswith("unconnected"):
                    nets[net.GetNetname()] = net  # Map net names to net objects
        return nets

    def ask_user_net_selection(self, net_names):
        class SelectAllDialog(wx.Dialog):
            def __init__(self, parent, net_names):
                super().__init__(parent, title="Select Nets")
                self.selected_nets = []
                self.net_names = net_names
                self.select_all = False
                self.init_ui()

            def init_ui(self):
                vbox = wx.BoxSizer(wx.VERTICAL)
                
                # Instruction
                label = wx.StaticText(self, label="Select the nets to add a suffix or prefix:")
                vbox.Add(label, flag=wx.ALL | wx.EXPAND, border=5)

                # Multi-choice list
                self.choice_list = wx.CheckListBox(self, choices=self.net_names)
                vbox.Add(self.choice_list, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

                # "Select All" checkbox
                self.select_all_checkbox = wx.CheckBox(self, label="Select All Nets")
                vbox.Add(self.select_all_checkbox, flag=wx.ALL, border=5)
                self.select_all_checkbox.Bind(wx.EVT_CHECKBOX, self.on_select_all)

                # Buttons
                hbox = wx.BoxSizer(wx.HORIZONTAL)
                ok_button = wx.Button(self, label="OK")
                cancel_button = wx.Button(self, label="Cancel")
                hbox.Add(ok_button, flag=wx.RIGHT, border=5)
                hbox.Add(cancel_button, flag=wx.RIGHT, border=5)
                vbox.Add(hbox, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

                ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
                cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

                self.SetSizer(vbox)
                self.SetSize((400, 500))
                self.Center()

            def on_select_all(self, event):
                if self.select_all_checkbox.IsChecked():
                    self.choice_list.SetChecked(range(len(self.net_names)))  # Select all
                    self.select_all = True
                else:
                    self.choice_list.SetChecked([])  # Deselect all
                    self.select_all = False

            def on_ok(self, event):
                self.selected_nets = [
                    self.net_names[i] for i in self.choice_list.GetCheckedItems()
                ]
                self.EndModal(wx.ID_OK)

            def on_cancel(self, event):
                self.selected_nets = []
                self.EndModal(wx.ID_CANCEL)

        # Use the dialog
        dialog = SelectAllDialog(None, net_names)
        if dialog.ShowModal() == wx.ID_OK:
            return dialog.selected_nets
        return []

    def ask_user_suffix_or_prefix(self):
        class SuffixOrPrefixDialog(wx.Dialog):
            def __init__(self, parent):
                super().__init__(parent, title="Suffix or Prefix")
                self.suffix_or_prefix = None
                self.mode = "suffix"  # Default to suffix
                self.init_ui()

            def init_ui(self):
                vbox = wx.BoxSizer(wx.VERTICAL)

                # Instruction
                label = wx.StaticText(self, label="Enter suffix or prefix and choose the mode:")
                vbox.Add(label, flag=wx.ALL | wx.EXPAND, border=5)

                # Input field
                hbox1 = wx.BoxSizer(wx.HORIZONTAL)
                label_input = wx.StaticText(self, label="Suffix/Prefix:")
                self.input_field = wx.TextCtrl(self)
                hbox1.Add(label_input, flag=wx.RIGHT, border=8)
                hbox1.Add(self.input_field, proportion=1)
                vbox.Add(hbox1, flag=wx.ALL | wx.EXPAND, border=5)

                # Mode radio buttons
                self.suffix_radio = wx.RadioButton(self, label="Add as Suffix", style=wx.RB_GROUP)
                self.prefix_radio = wx.RadioButton(self, label="Add as Prefix")
                vbox.Add(self.suffix_radio, flag=wx.ALL, border=5)
                vbox.Add(self.prefix_radio, flag=wx.ALL, border=5)

                # Buttons
                hbox2 = wx.BoxSizer(wx.HORIZONTAL)
                ok_button = wx.Button(self, label="OK")
                cancel_button = wx.Button(self, label="Cancel")
                hbox2.Add(ok_button, flag=wx.RIGHT, border=5)
                hbox2.Add(cancel_button, flag=wx.RIGHT, border=5)
                vbox.Add(hbox2, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

                ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
                cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

                self.SetSizer(vbox)
                self.SetSize((400, 300))
                self.Center()

            def on_ok(self, event):
                self.suffix_or_prefix = self.input_field.GetValue().strip()
                self.mode = "suffix" if self.suffix_radio.GetValue() else "prefix"
                self.EndModal(wx.ID_OK)

            def on_cancel(self, event):
                self.suffix_or_prefix = None
                self.EndModal(wx.ID_CANCEL)

        dialog = SuffixOrPrefixDialog(None)
        if dialog.ShowModal() == wx.ID_OK:
            return dialog.suffix_or_prefix, dialog.mode
        return None, None

    def strip_existing_suffix_or_prefix(self, net_name, mode):
        """
        Remove the existing suffix or prefix from a net name.
        """
        if "_" in net_name:
            if mode == "suffix":
                base, existing_suffix = net_name.rsplit("_", 1)
                if existing_suffix.isdigit():  # Check if suffix is numeric
                    return base
            elif mode == "prefix":
                existing_prefix, base = net_name.split("_", 1)
                if existing_prefix.isalnum():  # Check if prefix is alphanumeric
                    return base
        return net_name  # Return unchanged if no suffix/prefix

# Register the plugin
AddSuffixToSelectedComponentNetsPlugin().register()
