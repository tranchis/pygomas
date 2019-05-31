start.   

+flag (X,Y,Z): start 
  <-
  .print("In ASL,goto moving to: ",X,Y,Z); 
  //.goto(X,Y,Z);
  -start.

+cure(X,Y,Z) 
  <- 
  .print("Going to cure friend at: ",X,Y,Z);
  ?flag(A,B,C);
  //.goto(X,Y,Z).
  .goto(A,B,C).
  

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

