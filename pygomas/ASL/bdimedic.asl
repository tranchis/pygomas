+flag (X,Y,Z): team(100) 
  <-
  .goto(X,Y,Z).
  //.stop.

+flag (X,Y,Z): team(200) 
  <-
  //.wait(10000);
  .goto(X,Y,Z).
  //.stop.
