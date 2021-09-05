# VGB
VGB - Virtual Gantry Backers. A set of gcode_macro-based functions that counteract the effects of bimetallic expansion of aluminium profile + steel rail gantry in real time

# Thermal WHAT?
Read about thermal expansion in my older repo ![here](https://github.com/Deutherius/DFC-GBC). In short - metal expands with heat, different metals expand different amounts. Coupled metals expanding differently start bowing.

On a Voron V2.4 (mine is 300 mm spec), this manifests as a deeper "bowl" or "taco" shape when you take a bed mesh while the printer is hot, compared to the same printer when cold.

TODO:INSERT IMAGE OF TACO BOWL

The bed might have some small part in this, but it is an 8 mm thick slab of aluminium - it's not gonna bend *that* much. Proving that is easy - here are my bed meshes from one of my measure_thermal_behavior.py (get yours ![here!](https://github.com/alchemyEngine/measure_thermal_behavior) - or look for a newer one, if available) runs:

![thermal_quant_Deutherius#3295_2021-08-19_17-20-40 bed_diffmesh](https://user-images.githubusercontent.com/61467766/132133141-80db3704-913d-45c6-a7b7-08e79088ffff.png)

That's the difference between a bed mesh taken at ambient temps vs. bed mesh taken after heating the bed to 105 °C and soaking for 5 minutes after reaching temp (while the gantry is at the top Z to stay relatively cool). I would call this difference miniscule at best - at least compared to the difference between a hot bed mesh, and hot *printer* mesh:

![thermal_quant_Deutherius#3295_2021-08-19_17-20-40 mesh](https://user-images.githubusercontent.com/61467766/132133401-0146f0c2-24bf-4a71-8ced-9f5b64d2cccd.png)

That is after 1 hour of heating. During regular use, the mesh gets even worse. This is caused by the bimetallic expansion of the gantry - the bed mesh is measuring relative distance of the hotend from the bed. This can be counteracted in two parts - one is the bed mesh itself, the other is a global Z offset. My previous code (GBC - gantry bowing compensation) compensated for the global Z offset between prints - this works great (every print has the same first layer Z offset regardless of printer temperature), but only accounts for this effect *once*, while the gantry keeps bowing during the print as it heats up more. This can be "masked" by frame expansion compensation (either the real deal by ![alch3my](https://github.com/alchemyEngine/klipper/tree/work-frame-expansion-20210410), or my "dumb" gcode_macro version, DFC, linked at the start) - but you can notice that the edges of your bed have just a little bit more squish as the print progresses and the printer heats up:

![20210829_193641_arrow](https://user-images.githubusercontent.com/61467766/132133664-7a191730-e618-4a39-9cad-0ae62453b679.jpg)

Left side of the print was in the middle of the bed, while the right side was at the top right corner. Red arrow indicates overall print direction of the infill. In the top right corner, you can see the standard "valleys" forming that indicate that the toolhead is just a *little bit too close* to the bed. 

# The solution
You can quite easily (and stylishly!) solve the gantry bowing effect by getting a set of ![gantry backers](https://github.com/tanaes/whopping_Voron_mods/tree/main/extrusion_backers) for each affected extrusion. Then you will only have to account for the remaining thermal expansion of the entire frame in the Z direction with Frame Comp. If you do not, or can not, get a set of gantry backers, the code you will find here might hopefully provide an interesting alternative.

# VGB - Virtual Gantry Backers

## What is it?
A selection of gcode_macros for klipper (and a supporting script) that is a real-time expansion of my previous code, GBC.

## How does it work?

### In theory
GBC works by taking a "regular" bed mesh that works for you the best, finding its min-max range, and comparing any freshly taken bed mesh to that. Negative of the difference of min-max ranges is the new global Z offset adjustment. VGB uses the same principle, but the "freshly taken bed meshes" have to be available for any temperature of the printer during a print. Since the bimetallic bowing effect is linear with temperature, we can take two bed meshes at different temperatures and calculate a linear coefficient for each point of the mesh. With these coefficients and a base mesh, we can extrapolate and apply a mesh for *any* printer temperature at *any* time.

#### Hang on - this works?
Yes! Scroll all the way to the bottom for more info.

### In practice
Ideally, the bed mesh data that klipper currently uses could be altered on the fly from a gcode_macro. In reality, this data (and indeed *any* part of the `printer` variable) *cannot* be altered in this way. What we can do, however, is load meshes on the fly if they were previously saved in the config. That means that if we have a selection of bed meshes to choose from, say for every 0.1 °C of the thermistor we want to use for the compensation, we can get roughly the same functionality. Yes, that is *a lot* of bed meshes.

## How to "install"
You need 4 things:
1) A thermistor that measures the printer's temperature. Needs to be reasonably stable (i.e. no chamber thermistor in the Z chain that gets hot air blown at it *sometimes*) - frame thermistor in one of the vertical extrusions in your frame is perfect for this. (A thermistor measuring the X or Y extrusion temp is even better, but harder to install AND has a much wider range of expected temperatures, which increases the amount of bed meshes you need to generate)
2) As in GBC, a bed mesh that is the most regular for you and that your position_endstop is calibrated to. Name that mesh "REGULAR".
3) A mesh taken when the printer is cold, ideally at ambient temperature, and the temperature it was taken at (from the thermistor you intend to use, see point 1). Name that one "COLDx.x", where "x.x" is the temp, e.g. "COLD27.3".
4) A mesh taken when the printer is *hot*. Ideally finish a long print (2+ hours), take the print out, let the printer heat up again for at least 10 minutes, then take the mesh. Name that one "HOTx.x", e.g. "HOT36.6".

After you have satisfied all the above points, doublecheck that the meshes are in fact stored in the printer.cfg "DO NOT EDIT THIS BLOCK OR BELOW. The contents are auto-generated." section. We are going to edit that section - but don't worry, the contents will still be auto-generated, so it should be fine :). Included in this repo is a python script that will generate the new meshes for you, called `generate_VGB_meshes.py`. Download your printer.cfg (make a backup!), put it in the same folder as the script and call 

```python generate_VGB_meshes.py printer.cfg```

This will create a new printer.cfg (the old one will not be overwritten) chock full of generated meshes with the name "xx.x", e.g. "29.7". You can specify two additional arguments, the step at which the meshes are generated (0.1 °C by default) and extra temperatures to generate above and below the HOT and COLD mesh temps (2 °C by default) - i.e. `python generate_VGB_meshes.py printer.cfg 0.2 7` for step size of 0.2 °C and 7 extra °C.

Then just upload the new pinter.cfg to your printer (rename it to `printer.cfg` of course) and you are done with this part.

Final step is uploading VGB.cfg next to your printer.cfg and adding `[include VGB.cfg]` anywhere in the printer.cfg file.

You also need to turn on the M73 command generation in your slicer. In PS/SS, this is the "Supports remaining times" option in the printer settings page.

That's it! You can verify that VGB is working with the QUERY_VGB macro. You can also enable or disable the function with "SET_VGB ENABLE=1" or "SET_VGB ENABLE=0".

# The end

Caution, blah blah blah



# Appendix A - Experimental Evaluation of the linear bed mesh extrapolation
I have conducted several experiments with a slightly altered measure_thermal_behavior.py script that takes a bed mesh every 2 minutes in addition to all the other measurements. I have also added temperature sensors to the X and Y extrusions. 

![Sensors_MeshRange_over_Time](https://user-images.githubusercontent.com/61467766/132134633-2bbddf12-113b-46cf-8dbd-29aa6da16198.png)

In the included chart, you can see how the mesh min-max range ("bowl-iness") increases with temperature of all sensors. For the first 60 minutes, the bed is heated up to 105 °C. Then the bed heater is turned off for 30 minutes, then turned back on for 30 minutes, and finally turned off again for another 30 minutes. Note that the bed mesh range tends to increase slightly *just* as the bed heater is turned off and the bed starts cooling down - there is a significant hysteresis effect in play here, the cause of which is unknown to me yet.

I have taken the bed mesh at T=0 minutes, i.e. heatsoaked bed, but cold printer, and the bed mesh at T=60 minutes, i.e. as the printer was at its hottest point. Between these two meshes, I have calculated the aforementioned point-wise linear coefficients and extrapolated a bed mesh for every temperature measured in the course of the experiment. That means I can compare the extrapolated meshes with real, measured meshes. The absolute error in the form of a heatmap is in the next chart:

![AbsError_heating](https://user-images.githubusercontent.com/61467766/132134771-08b263a5-b823-48ae-8e5d-b46cf62c59ba.png)

The red outlines specify which meshes were with the bed heater on. You can see that the absolute error between extrapolated and measured meshes is rather low when the bed heater is on, but increases when the bed is cooling down. Most of the error accumulates within the top rows, which seems to me to be dependent on the way in which the measured bed meshes were taken - left-to-right, bottom-to-top. Speculation only, I have not yet tried to reverse the bed mesh point order. Good news is that we don't care about how the predicted bed meshes look while the printer is cooling down, only while it's heating up - and those look great. Maximum absolute error of 11.9 microns.

Also note that the first and last mesh in the first "heating" section have 0 error - that is because the linear coefficients were calculated using these two meshes, ergo they fit perfectly.

In terms of mean square error over all points, the chart looks like this

![MSE_over_time](https://user-images.githubusercontent.com/61467766/132135076-9acc0e8d-3b8a-425c-ba99-b516afd4cc4f.png)

Once again, heating sections have low error, cooling sections have high error.






