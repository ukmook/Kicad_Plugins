This tool is designed to back annotate net labels from pcbnew to eschema.
I made this after a copy and paste on eschema left the same net labels.
Usage.
Highlight the components either on the schematic or the PCB run 
the plugin, pick the nets or select all then deslect the ones 
you dont want to change, press ok, add the label i.e. 1 or 2 etc,
then select the radio button (Prefix or Suffix), press OK.
Check the nets of the components. 
Go to eschema, Tools & select update schematic from PCB.
Select only net names and press OK. 

Copy the add_suffix_selected_net_labels.py and icon to the 
Kicad/8.0/scripting/plugins/ directory restart or reload plugins. 
