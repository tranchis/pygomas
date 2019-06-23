+flag(X,Y,Z): team(100) 
  <-
  .print("ALLIED FIELDOP: ",X,Y,Z); 
  .goto(X,Y,Z).
  //.goto(16,0,38).
  //.stop.


+flag(X,Y,Z): team(200) 
  <-
  //.wait(10000);
  //.goto(16,0,38).
  .goto(X,Y,Z).
  //.stop.

