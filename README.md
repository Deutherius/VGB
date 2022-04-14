# VGB - Virtual Gantry Backers
A set of gcode_macro-based functions that counteract the effects of bimetallic expansion of aluminium profile + steel rail gantry in real time.
Part of the [Thermal Expansion Compensation Package](https://github.com/Deutherius/TECPac).

# Thermal WHAT?
Read about thermal expansion in [whoppingpochard's amazing repo](https://github.com/tanaes/whopping_Voron_mods/tree/main/extrusion_backers). In short - metal expands with heat, different metals expand different amounts. Coupled metals expanding differently start bowing (exactly like the bimetallic strip in your electric kettle or clothes iron).

On a Voron 2.4 (mine is 300 mm spec), this manifests as a deeper "bowl" or "taco" shape when you take a bed mesh while the printer is hot, compared to the same printer when cold.

![hot_mesh](https://user-images.githubusercontent.com/61467766/133098592-8903d003-e97f-465b-8e1f-5cab74fb9ad1.JPG)
![cold_mesh](https://user-images.githubusercontent.com/61467766/133098588-81abefcd-0faf-4dbf-8c21-299abb6d7d9c.JPG)

The bed might have some small part in this, but it is an 8 mm thick slab of aluminium - it's not gonna bend *that* much. Proving that is easy - here are bed meshes from one of my measure_thermal_behavior.py (get yours [here!](https://github.com/alchemyEngine/measure_thermal_behavior) - or look for a newer one, if available) runs:

![thermal_quant_Deutherius#3295_2021-08-19_17-20-40 bed_diffmesh](https://user-images.githubusercontent.com/61467766/132133141-80db3704-913d-45c6-a7b7-08e79088ffff.png)

That's the difference between a bed mesh taken at ambient temps vs. bed mesh taken after heating the bed to 105 °C and soaking for 5 minutes after reaching temp (while the gantry is at the top Z to stay relatively cool). I would call this difference miniscule at best - at least compared to the difference between a hot bed mesh, and hot *printer* mesh:

![thermal_quant_Deutherius#3295_2021-08-19_17-20-40 mesh](https://user-images.githubusercontent.com/61467766/132133401-0146f0c2-24bf-4a71-8ced-9f5b64d2cccd.png)

That is after 1 hour of heating. During regular use, the mesh gets even worse. This is caused by the bimetallic expansion of the gantry - the bed mesh is measuring relative distances of the toolhead from the bed.

### What does this look like in a print?

![20210816_195655](https://user-images.githubusercontent.com/61467766/133771976-0ac395e4-e406-409a-a4e9-af5b65df423e.jpg)

What you see on the left is a part from a 7-hour print job with a first layer time of 22 minutes. The right part was printed alone, with a first layer of 1 minute and 45 seconds. All settings and printer state was the same (cold) for both prints. Both parts were close to the center of the bed, where the gantry bowing is most prominent - but in the part on the right, the bowing happens over multiple layers, masking the effect, while on the left part, it mostly happens over the first few layers (1-3) and causes the subsequent layers to be significantly higher than expected.

**Part of this issue is also caused by the vertical frame expansion, which you can read more on [here](https://github.com/Deutherius/DFC). Both issues compound each other and the image serves as a nice visual aid, which is why I use the same image in both repos.**

### Doesn't the bed mesh itself solve this issue?

Yes, but only when the conditions are static. If you heatsoak your machine to the point of thermal equilibrium, bed mesh basically solves this issue. Problem is, on larger machines, reaching thermal equilibrium can take *hours*. Ain't nobody got time for that.
But if you don't heatsoak for long enough, the bed mesh that you take just before a print gets out of date *fast*.

# The solution
You can quite easily (and stylishly!) alleviate the gantry bowing effect by getting a set of [gantry backers](https://github.com/tanaes/whopping_Voron_mods/tree/main/extrusion_backers) for each affected extrusion. Two problems with this solution:
1) It only solves the issue completely on small footprint machines (think max 250 mm^2), on larger machines the issue is only lessened, and
2) It can be quite gucci ($$), especially if you go for the titanium version ($$$$$$).

### So are we screwed?

Nope! As stated before, you can correct for gantry bowing with the use of a bed mesh. Can't use a static one, but if you had a *dynamic bed mesh*...

# VGB - Virtual Gantry Backers

## How does it work?

### In theory
Since the bimetallic bowing effect is linear, it is possible to take two bed meshes at different temperatures and calculate a linear thermal expansion coefficient for each point of the mesh (similar to [frame comp](https://github.com/alchemyEngine/klipper/tree/work-frame-expansion-20210410)/[dumb frame comp](https://github.com/Deutherius/DFC/blob/main/README.md)). With these coefficients and a base mesh, it is possible to extrapolate and apply a mesh for *any* printer temperature at *any* time.

#### Hang on - this works?
Yes! Scroll all the way to the bottom for more info.

### In practice
Ideally, the bed mesh data that klipper currently uses could be altered on the fly from a gcode_macro. In reality, this data (and indeed *any* part of the `printer` variable) *cannot* be altered in this way. What we can do, however, is load meshes on the fly if they were previously saved in the config. That means that if we have a selection of bed meshes to choose from, say for every 0.1 °C of the thermistor we want to use for the compensation, we can get roughly the same functionality. Yes, that is *a lot* of bed meshes.

![meshes](https://user-images.githubusercontent.com/61467766/133106401-00e3681f-e2ff-4f52-ad80-2a0b5eb251d3.JPG)

## How to set things up

### If you intend to change the [relative reference index](https://github.com/Deutherius/Gantry-bowing-induced-Z-offset-correction-through-relative-reference-index), do it first! Otherwise you will have to redo the next steps :)

You need 4 things:
1) A thermistor that measures the printer's temperature. Needs to be reasonably stable (i.e. no chamber thermistor in the Z chain that gets hot air blown at it *sometimes*) - frame thermistor in one of the vertical extrusions in your frame is perfect for this. (A thermistor measuring the X or Y extrusion temp is even better, but harder to install AND has a much wider range of expected temperatures, which increases the amount of bed meshes you need to generate)
2) A mesh taken when the printer is relatively cold, ideally after a short heatsoak (~10 minutes) from ambient temperature, and the temperature it was taken at (measured at the thermistor you intend to use, see point 1). Name that one "COLDx.x", where "x.x" is the temp, e.g. "COLD27.3".
3) A mesh taken when the printer is *hot*. Ideally finish a long print (2+ hours), take the print out, let the printer heat up again for at least 10 minutes, then take the mesh. Name that one "HOTx.x", e.g. "HOT36.6".
4) Additionally, you might want to take a mesh at a different temperature for testing purposes. This should be taken while the printer is heating up (not cooling down!), and should be named "TESTx.x", e.g. "TEST31.2". This step is not necessary for VGB to function, it's just for peace of mind.

After you have satisfied the above points, doublecheck that the meshes are in fact stored in the printer.cfg "DO NOT EDIT THIS BLOCK OR BELOW. The contents are auto-generated." section. We are going to edit that section - but don't worry, the contents will still be auto-generated, so it should be fine :). Included in this repo is a python script that will generate the new meshes for you, called `generate_VGB_meshes.py`. you will need python 3 and numpy to run it. Download your printer.cfg (make a backup!), put it in the same folder as the script and call 

```python3 generate_VGB_meshes.py printer.cfg```

This will create a new printer.cfg (the old one will not be overwritten) chock full of generated meshes with the name "xx.x", e.g. "29.7". You can specify two additional arguments, the step at which the meshes are generated (0.1 °C by default) and extra temperatures to generate above and below the HOT and COLD mesh temps (2 °C by default) - i.e. `python3 generate_VGB_meshes.py printer.cfg 0.2 7` for step size of 0.2 °C and 7 extra °C.

If you had a "TEST" bed mesh in your config, you should see an additional output from the script in the console. This output contains a matrix of absolute errors between the extrapolated mesh and the TEST mesh, a mean square error over all points and a maximum absolute error (i.e. the largest value from the matrix). You should see MSE on the order of 2e-5 and a maximum absolute error of roughly 20 microns. If you see much more than that (i.e. more than 50 microns max abs error), something might be wrong, contact me just to be safe.

Then just upload the new printer.cfg to your printer (rename it to `printer.cfg` of course) and you are done with this part. *Make sure there is one bed mesh named "default" in the config, otherwise Klipper might flip out.*

Next step is uploading VGB.cfg next to your printer.cfg and adding `[include VGB.cfg]` anywhere in the printer.cfg file. Finally, open VGB.cfg and fill in your temperature details (minimum generated temp, maximum generated temp and step size).

That's it! VGB will start loading temperature-based meshes right after Klipper starts, and then every 10 seconds. You can verify that VGB is working with the QUERY_VGB macro (or just look at your current mesh :). You can also enable or disable the function with "SET_VGB ENABLE=1" or "SET_VGB ENABLE=0". If you disable VGB, the last mesh will stay loaded and no further changes will be made. If you then turn VGB back on, the mesh will instantly change, so beware! This could cause a nozzle strike if you are not careful. Ideally, you never want to turn the feature on or off *during* a print.


### IMPORTANT - DISABLE FADE

Otherwise all of this black magic will only be applied to the first few millimeters, and the rest of the print will be as curved as your gantry. Just comment out `fade_start:` and `fade_end:` in the `[bed_mesh]` section.

### EVEN MORE IMPORTANT - SWITCHING BUILDPLATES

This is a custom-fit solution that I have at this point only verified to work **with the entire system as it was during the setup!** If you swap a different buildplate in, I cannot guarantee that it will work!

# The end

That's it! However bendy your gantry gets, this function will compensate for it. The usual warnings apply - be careful, have your hand on the E-stop just in case, watch the printer (at least at first)...
Additionally, I strongly urge you to change your relative reference index from the center of the bed to one of the corners, which will eliminate most temperature-based global Z offset changes, see [here](https://github.com/Deutherius/Gantry-bowing-induced-Z-offset-correction-through-relative-reference-index).



# Appendix A - Experimental Evaluation of the linear bed mesh extrapolation
I have conducted several experiments with a slightly altered measure_thermal_behavior.py script that takes a bed mesh every 2 minutes in addition to all the other measurements. I have also added temperature sensors to the X and Y extrusions. 

![Sensors_MeshRange_over_Time](https://user-images.githubusercontent.com/61467766/132134633-2bbddf12-113b-46cf-8dbd-29aa6da16198.png)

In the included chart, you can see how the mesh min-max range ("bowl-iness") increases with temperature of all sensors. For the first 60 minutes, the bed is heated up to 105 °C. Then the bed heater is turned off for 30 minutes, then turned back on for 30 minutes, and finally turned off again for another 30 minutes. Note that the bed mesh range tends to increase slightly *just* as the bed heater is turned off and the bed starts cooling down - there is a significant hysteresis effect in play here, the cause of which is unknown to me yet.

I have taken the bed mesh at T=0 minutes, i.e. heatsoaked bed, but cold printer, and the bed mesh at T=60 minutes, i.e. as the printer was at its hottest point. Between these two meshes, I have calculated the aforementioned point-wise linear coefficients and extrapolated a bed mesh for every temperature measured in the course of the experiment. That means I can compare the extrapolated meshes with real, measured meshes. The absolute error in the form of a heatmap is in the next chart:

![AbsError_heating](https://user-images.githubusercontent.com/61467766/132134771-08b263a5-b823-48ae-8e5d-b46cf62c59ba.png)

The red outlines specify which meshes were with the bed heater on. You can see that the absolute error between extrapolated and measured meshes is rather low when the bed heater is on, but increases when the bed is cooling down. Most of the error accumulates within the top rows, which seems to me to be dependent on the way in which the measured bed meshes were taken - left-to-right, bottom-to-top. Speculation only, I have not yet tried to reverse the bed mesh point order. Good news is that we don't care about how the predicted bed meshes look while the printer is cooling down, only while it's heating up - and those look great. Maximum absolute error of 17.7 microns with a mean absolute error of 4 microns over the entire heating period.

Also note that the first and last mesh in the first "heating" section have 0 error - that is because the linear coefficients were calculated using these two meshes, ergo they fit perfectly.

In terms of mean square error over all points, the chart looks like this

![MSE_over_time](https://user-images.githubusercontent.com/61467766/132135076-9acc0e8d-3b8a-425c-ba99-b516afd4cc4f.png)

Once again, heating sections have low error, cooling sections have high error.






