#ifndef GAME_H
#define GAME_H

#include "world.h"

class Graphics;

class Game{
public:
    Game();
    ~Game();
private:
    void gameLoop();
    void draw(Graphics &graphics);

    World _world;
};

#endif // GAME_H
