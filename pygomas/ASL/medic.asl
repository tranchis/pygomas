+flag (X,Y,Z): team(100) 
  <-
  //.goto(16,0,38).
  .goto(X,Y,Z).

+flag (X,Y,Z): team(200) 
  <-
  .wait(10000);
  //.print("In ASL,TEAM_AXIS patrolling around: ",X,Y,Z); 
  //.create_control_points(X,Y,Z,4,5).
  //.goto(16,0,38).
  .goto(X,Y,Z).

+cure(X,Y,Z) 
  <- 
  .print("Going to cure friend at: ",X,Y,Z);
  //?flag(A,B,C);
  //.goto(A,B,C).
  .goto(X,Y,Z).
  

+target_reached(X,Y,Z)
//+target_reached(X,Y,Z): cure(X1,Y2,Z2) & X==X1 & Z==Z1
  <- 
  .cure;
  .print("In ASL, Medic cured at :",X,Y,Z);
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
  //?myMedics(A);
  //.nth(0,A,M);
  //.print(M);
  //.send(M, tell,cure(X,Y,Z));
  -first_call(on);
  +first_call(off);
  -health(H).

