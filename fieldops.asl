+flag (X,Y,Z): team(100) 
  <-
  .print("In ASL,TEAM_ALLIED goto moving to: ",X,Y,Z); 
  //.goto(X,Y,Z).
  .goto(16,0,38).

+flag (X,Y,Z): team(200) 
  <-
  .goto(X,Y,Z).

+target_reached(X,Y,Z)
//+target_reached(X,Y,Z): cure(X1,Y2,Z2) & X==X1 & Z==Z1
  <- 
  .reload;
  .print("In ASL, Fieldop reloaded at :",X,Y,Z);
  -target_reached(X,Y,Z).

+enemies_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z) 
<- 
.shoot(5,X,Y,Z);
-enemies_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z).

+health(H): threshold_health(T) & H <= T 
//+health(H): threshold_health(T) & H <= T & first_call(on) &team(100)
  <- 
  .get_medics;
  ?position(X,Y,Z);
  ?myMedics(A);
  .nth(0,A,M);
  .print(M);
  .send(M, tell,cure(X,Y,Z));
  -first_call(on);
  +first_call(off);
  -health(H).