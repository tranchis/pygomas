//100 is TEAM_ALLIED 
//200 is TEAM_AXIS 
+base (X,Y,Z)  
  <-
  +first_call(on);
  .print ("In ASL, my base at: ",X,Y,Z).

+team (X)  
  <-
  //.get_medics;
  //.get_fieldops;
  .print ("In ASL, my team is: ",X).

+flag (X,Y,Z): team(100) & first_call(on)
  <-
  .print("In ASL,TEAM_ALLIED goto moving to: ",X,Y,Z); 
  -first_call(on);
  +first_call(off);
  .goto(X,Y,Z).
  //.goto(16,0,38).

+flag (X,Y,Z): team(200) 
  <-
  .wait(10000);
  .create_control_points(X,Y,Z,4,5);
  //.stop;
  .goto(X,Y,Z).
  //.print("In ASL,TEAM_AXIS patrolling around: ",X,Y,Z). 

+flag_taken: team(100) 
  <-
  .print("In ASL, TEAM_ALLIED flag_taken");
  ?base(X,Y,Z);
  //.print("going to base at position: ",X,Y,Z);
  .goto(81,0,68).
  //.goto(X,Y,Z).
  //.stop.

+flag_taken: team(200) 
  <-
  .print("In ASL, TEAM_AXIS flag_taken");
  ?base(X,Y,Z);
  .print("going to base at position: ",X,Y,Z);
  .goto(X,Y,Z).

-flag_taken
 <-
 .print("Lost flag").

+target_reached(X,Y,Z): X=81 & Z=68
  <- 
  ?flag(A,B,C);
  .print ("THE flag is at ",A,B,C);
  .print("In ASL, reached with flag, target at :",X,Y,Z);
  .goto(16,0,38).


+target_reached(X,Y,Z): patrolling(off)
  <- 
  .print("In ASL, reached target at :",X,Y,Z).
  //-target_reached(X,Y,Z).

+target_reached(X,Y,Z): patrolling(on)  
  <- 
  ?patroll_point(P);
  //.print("In ASL, Reached control point :", P);
  -+patroll_point(P+1);
  -target_reached(X,Y,Z).

+control_points(C) 
  <- 
  //.print("In ASL, patrol points  :",C);
  .length(C,L);
  +total_control_points(L);
  +patrolling(on);
  +patroll_point(0).

+patroll_point(P): total_control_points(T) & P<T  
  <-
  //.print("Patrolling");
  ?control_points(C);
  .nth(P,C,A);
  .nth(0,A,X);
  .nth(1,A,Y);
  .nth(2,A,Z);
  .goto(X,Y,Z).

+patroll_point(P): total_control_points(T) & P==T 
  <-
  //.print("Patrolling again");
  -patroll_point(P);
  +patroll_point(0).

+name(X) 
  <- 
  //.print("In ASL,setting name to:",X);
  -name(X).

//+health(H): threshold_health(T) & H <= T & team(100)
+health(H): threshold_health(T) & H <= T & first_call(on) &team(100)
  <- 
  .print("Injured. My health",H);
  .get_medics;
  ?myMedics(All_medics);
  .nth(0,All_medics,M);
  .print(M);
  ?position(X,Y,Z);
  .send(M, tell,cure(X,Y,Z));
  -first_call(on);
  +first_call(off);
  -health(H). 

//+health(H): threshold_health(T) & H <= T & first_call(on) &team(200)
  //<-
  //.get_medics;
  //.print("Injured. My health",H);
  //?flag(X,Y,Z);
  //?myMedics(All_medics);
  ////?base(X,Y,Z);
  ////.print("Going back to base at" ,X,Y,Z);
  ////?position(X,Y,Z);
  //.nth(0,All_medics,M);
  //.print(M);
  //.send(M, tell,cure(X,Y,Z));
  //.goto(X,Y,Z);
  //-first_call(on);
  //+first_call(off);
  //-health(H).  

+ammo(A): threshold_ammo(T) & A <= T & team(200) & first_call(on)
  <- 
  //.get_fieldops;
  .stop;
  ?position(X,Y,Z);
  .print("Out of Ammo at",X,Y,Z, A);
  ?myFieldops(All_fieldops);
  .nth(0,All_fieldops,F);
  .send(F, tell,need_ammo(X,Y,Z));
  //.goto(X,Y,Z);
  .print("CALLING FIELDOP",F);
  -first_call(on);
  +first_call(off);
  -ammo(A).  

+pack_taken(Pack,Quantity): Pack == ammo 
  <-
  .print("In ASL,taking ammo pack");
  .print("Increase ammo by: ",Quantity);
  -pack_taken(Pack,Quantity).

+pack_taken(Pack,Quantity): Pack == medic 
  <-
  .print("In ASL,taking medic pack");
  .print("Increase health by: ",Quantity);
  -pack_taken(Pack,Quantity).

+enemies_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z): Type<1000
//+enemies_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z): team(200) & Type<1000
  <- 
  //.print("In ASL,setting enemies_in_fov with ID:",ID);
  //.print("with params :");
  //.print("Type :",Type);
  //.print("Angle :",Angle);
  //.print("Distance :",Distance);
  //.print("Health :",Health);
  //.print("X :",X);
  //.print("Y :",Y);
  //.print("Z :",Z);
  .shoot(2,X,Y,Z);
  //.print("shooting here");
  -enemies_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z).

+friends_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z) 
  <- 
//.print("In ASL,setting friends_in_fov with ID:",ID);
//.print("with params :");
//.print("Type :",Type);
//.print("Angle :",Angle);
//.print("Distance :",Distance);
//.print("Health :",Health);
//.print("X :",X);
//.print("Y :",Y);
//.print("Z :",Z);
-friends_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z).

//+packs_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z) 
  //<- 
  //.print("In ASL,setting packs_in_fov with ID:",ID);
  //.print("with params :");
  //.print("Type :",Type);
  //.print("Angle :",Angle);
  //.print("Distance :",Distance);
  //.print("Health :",Health);
  //.print("X :",X);
  //.print("Y :",Y);
  //.print("Z :",Z);
  //-packs_in_fov(ID,Type,Angle,Distance,Health,X,Y,Z).

