 //TEAM_AXIS

+flag (X,Y,Z): team(200) 
  <-
  .create_control_points(X,Y,Z,25,5);
  .wait(5000).

+control_points(C) 
  <- 
  .length(C,L);
  +total_control_points(L);
  +patrolling;
  +patroll_point(0);
  .print("Got control points").


+target_reached(X,Y,Z): patrolling & team(200) 
  <- 
  ?patroll_point(P);
  -+patroll_point(P+1);
  -target_reached(X,Y,Z).

+patroll_point(P): total_control_points(T) & P<T 
  <-
  ?control_points(C);
  .nth(P,C,A);
  .nth(0,A,X);
  .nth(1,A,Y);
  .nth(2,A,Z);
  .goto(X,Y,Z).

+patroll_point(P): total_control_points(T) & P==T
  <-
  -patroll_point(P);
  +patroll_point(0).


//TEAM_ALLIED 

+flag (X,Y,Z): team(100) 
  <-
  .goto(X,Y,Z).

+flag_taken: team(100) 
  <-
  .print("In ASL, TEAM_ALLIED flag_taken");
  ?base(X,Y,Z);
  .goto(X,Y,Z).

+enemies_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z)
  <- 
  .shoot(3,X,Y,Z).