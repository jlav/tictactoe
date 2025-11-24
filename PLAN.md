Hi!

I'm going to create a simple 2 player online game of tic tac toe, with real time updates.

I'm a better backend developer than frontend, so I'll focus my time there.
I think it would be really fun to actually deploy this application to a real cloud environment.

Here's my game plan: I'll spend an hour and 45 minutes on the project, then
take 15 minutes at the end for the readme.

I'll start simple with a basic backend server that can handle game state and player moves in memory,
publish events via websockets, and a minimal frontend to interact with the game.

Then I'd like to get it deployed to a cloud provider. I'll user Render since
it's a PaaS and it's free. I haven't used Render before, so I'll be demonstrating learning under
pressure a bit.

That's probably enough to consume my time, but if I have time left over, I'll work on
adding persistence and maybe pubsub style event broadcasting so that it can autoscale
and use multiple instances.