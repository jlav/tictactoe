# TicTacToe - PR REVIEW TEST

A simple, 2 player online Tic Tac Toe game. Try it out at [tictactoe.jlaverty.me](https://tictactoe.jlaverty.me).

## Running the App Locally

Install `uv`, if you haven't already: https://docs.astral.sh/uv/getting-started/installation/

Sync dependencies with
```
uv sync
```

Start the server with:
```
uv run fastapi dev main:app
```

## Approach

I wanted to build a tic-tac-toe app that felt a little more "real" than one that just ran on my local machine.
I decided to build a simple tic-tac-toe game that updated in real time, and I had a stretch goal of deploying it to a cloud provider.

I chose FastAPI for the backend mostly out of familiarity, and I used WebSockets for real-time updates.
My skillset is with backend development and infrastructure, so I didn't spend much time on the frontend at all.
Because I was planning to deploy to a cloud provider that I wasn't familiar with, I only prioritized basic gameplay features
to give myself more time to focus on deployment.

I initially said that after getting the app deployed, I would add persistence. I remembered midway through
that I have an old domain name hanging around, and thought it would be nice to set up a subdomain to serve the app.

## AI Tools

I used Claude Code to scaffold and build the entire application. I lean on Claude Code's plan mode a lot - I can give
fairly simple instructions and make sure that it's coming up with a coherent plan before I let it start writing code.
I also generally avoid automatically accepting edits so that I get a chance to review everything that it writes.
A quick file-by-file skim is easier to review than trying to understand a large chunk of code all at once.

I also have GitHub Copilot enabled for text completions in PyCharm.

## If I Had More Time
If I had more time, I would love to add persistence so that games could survive server restarts, and also
broadcast events via a pubsub system so that the app could scale to multiple instances.

I also would love to have added some more basic features like resetting the game state without having to create a new room,
and maybe a lobby system to see active games. I started on the reset feature, but Claude wasn't able to knock it out in
a couple of tries. With the clock ticking I decided to keep working on the domain name.

Last, there's no security at all. You can spoof which player you are to cheat. I'd like to at least add UUIDs for the
as player identifiers that are kept secret so that it's not trivial to cheat.


