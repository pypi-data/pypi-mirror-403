\* Source Pyomo model name=Model *\

min 
objective:
+35 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0)
+35 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_1)
+35 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_2)
+35 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_3)
+35 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_4)
+35 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_5)
+35 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_6)
+35 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_7)
+35 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_8)

s.t.

c_e_BusBlock_balance((_connection____pv0____house_1_)_0)_:
-1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_0)
-1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
+1 flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_0)
= 0

c_e_BusBlock_balance((_connection____pv0____house_1_)_1)_:
-1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_1)
-1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1)
+1 flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_1)
= 0

c_e_BusBlock_balance((_connection____pv0____house_1_)_2)_:
-1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_2)
-1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_2)
+1 flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_2)
= 0

c_e_BusBlock_balance((_connection____pv0____house_1_)_3)_:
-1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_3)
-1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_3)
+1 flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_3)
= 0

c_e_BusBlock_balance((_connection____pv0____house_1_)_4)_:
-1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_4)
-1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_4)
+1 flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_4)
= 0

c_e_BusBlock_balance((_connection____pv0____house_1_)_5)_:
-1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_5)
-1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_5)
+1 flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_5)
= 0

c_e_BusBlock_balance((_connection____pv0____house_1_)_6)_:
-1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_6)
-1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_6)
+1 flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_6)
= 0

c_e_BusBlock_balance((_connection____pv0____house_1_)_7)_:
-1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_7)
-1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_7)
+1 flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_7)
= 0

c_e_BusBlock_balance((_connection____pv0____house_1_)_8)_:
-1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_8)
-1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_8)
+1 flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_8)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_0)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_0)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
+1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_1)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_1)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1)
+1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_2)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_2)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_2)
+1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_2)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_3)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_3)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_3)
+1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_3)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_4)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_4)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_4)
+1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_4)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_5)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_5)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_5)
+1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_5)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_6)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_6)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_6)
+1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_6)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_7)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_7)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_7)
+1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_7)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_8)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_8)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_8)
+1 flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_8)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_0)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0)
+1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_1)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_1)
+1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_2)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_2)
+1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_2)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_3)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_3)
+1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_3)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_4)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_4)
+1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_4)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_5)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_5)
+1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_5)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_6)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_6)
+1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_6)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_7)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_7)
+1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_7)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_8)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_8)
+1 flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_8)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_0)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_1)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_1)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_2)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_2)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_3)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_3)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_4)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_4)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_5)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_5)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_6)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_6)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_7)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_7)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_8)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_8)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_0)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_1)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_1)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_2)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_2)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_2)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_3)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_3)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_3)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_4)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_4)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_4)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_5)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_5)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_5)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_6)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_6)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_6)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_7)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_7)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_7)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_8)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_8)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_8)
= 0

c_e_BusBlock_balance((_input____demand0____house_1_)_0)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_0)
= 10

c_e_BusBlock_balance((_input____demand0____house_1_)_1)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_1)
= 10

c_e_BusBlock_balance((_input____demand0____house_1_)_2)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_2)
= 10

c_e_BusBlock_balance((_input____demand0____house_1_)_3)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_3)
= 10

c_e_BusBlock_balance((_input____demand0____house_1_)_4)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_4)
= 10

c_e_BusBlock_balance((_input____demand0____house_1_)_5)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_5)
= 10

c_e_BusBlock_balance((_input____demand0____house_1_)_6)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_6)
= 10

c_e_BusBlock_balance((_input____demand0____house_1_)_7)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_7)
= 10

c_e_BusBlock_balance((_input____demand0____house_1_)_8)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_8)
= 10

bounds
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_0) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_1) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_2) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_3) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_4) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_5) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_6) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_7) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____demand0____house_1_)_8) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_1) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_2) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_3) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_4) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_5) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_6) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_7) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_8) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_2) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_3) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_4) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_5) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_6) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_7) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_8) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_1) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_2) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_3) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_4) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_5) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_6) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_7) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_8) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_0) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_1) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_2) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_3) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_4) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_5) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_6) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_7) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_8) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_2) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_3) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_4) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_5) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_6) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_7) <= +inf
   0 <= flow((_connection____pv0____house_1_)_(_distribution____ElectricityCarrier____house_1_)_8) <= +inf
   0 <= flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_0) <= 0.0
   0 <= flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_1) <= 0.0
   0 <= flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_2) <= 0.0
   0 <= flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_3) <= 0.0
   0 <= flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_4) <= 0.0
   0 <= flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_5) <= 0.0
   0 <= flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_6) <= 18292.716169609103
   0 <= flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_7) <= 94032.63946595292
   0 <= flow((_source____pv0____house_1_)_(_connection____pv0____house_1_)_8) <= 151948.6507974122
end
