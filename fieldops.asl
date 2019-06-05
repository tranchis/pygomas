+flag(X,Y,Z): team(100) 
  <-
  .print("ALLIED FIELDOP: ",X,Y,Z); 
  //.goto(X,Y,Z).
  .goto(16,0,38).


+flag(X,Y,Z): team(200) 
  <-
  .print("AXIS FIELDOP").
  //.goto(X,Y,Z).

+target_reached(X,Y,Z)
//+target_reached(X,Y,Z): cure(X1,Y2,Z2) & X==X1 & Z==Z1
  <- 
  .reload;
  .print("In ASL, Fieldop reloaded at :",X,Y,Z);
  -target_reached(X,Y,Z).

+enemies_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z) 
<- 
//.shoot(5,X,Y,Z);
-enemies_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z).

+need_ammo(X,Y,Z) 
  <- 
  .print("Going to give ammo to friend at: ",X,Y,Z);
  //?flag(A,B,C);
  //.goto(A,B,C).
  .goto(X,Y,Z).
  

