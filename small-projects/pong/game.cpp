#include <SDL2/SDL.h>
#include "graphics.h"
#include "input.h"

#include "game.h"

namespace{
    const int FPS = 60;
    const int MAX_FRAME_TIME = 1000 / FPS;
}

Game::Game(){
    SDL_Init(SDL_INIT_EVERYTHING);
    this->gameLoop();
}

Game::~Game(){
    SDL_Quit();
}

void Game::gameLoop(){
    Graphics graphics;
    Input input;
    SDL_Event event;

    const SDL_Scancode pauseKey = SDL_SCANCODE_ESCAPE;
    const SDL_Scancode startKey = SDL_SCANCODE_SPACE;
    const SDL_Scancode modeKey = SDL_SCANCODE_P;
    const SDL_Scancode difficultyKey = SDL_SCANCODE_O;
    const SDL_Scancode up1Key = SDL_SCANCODE_W;
    const SDL_Scancode down1Key = SDL_SCANCODE_S;
    const SDL_Scancode up2Key = SDL_SCANCODE_UP;
    const SDL_Scancode down2Key = SDL_SCANCODE_DOWN;

    this->_world = World();

    int LAST_UPDATE_TIME = SDL_GetTicks();

    while(true){
        // Handle inputs
        input.beginNewFrame();
        if(SDL_PollEvent(&event)){
            if(event.type == SDL_KEYDOWN){
                if(event.key.repeat == 0){
                    input.keyDownEvent(event);
                }
            }else if(event.type == SDL_KEYUP){
                input.keyUpEvent(event);
            }else if(event.type == SDL_QUIT){
                return;
            }
        }
        if(input.wasKeyPressed(pauseKey)){
            return;
        }else if(input.wasKeyPressed(startKey)){
            this->_world.startGame();
        }else if(input.wasKeyPressed(modeKey)){
            this->_world.changeGameMode();
        }else if(input.wasKeyPressed(difficultyKey)){
            this->_world.changeDifficulty();
        }
        if(input.isKeyHeld(up1Key)){
            this->_world.moveP1(0);
        }else if(input.isKeyHeld(down1Key)){
            this->_world.moveP1(2);
        }
        if(input.isKeyHeld(up1Key) == input.isKeyHeld(down1Key)){
            this->_world.moveP1(1);
        }
        if(input.isKeyHeld(up2Key)){
            this->_world.moveP2(0);
        }else if(input.isKeyHeld(down2Key)){
            this->_world.moveP2(2);
        }
        if(input.isKeyHeld(up2Key) == input.isKeyHeld(down2Key)){
            this->_world.moveP2(1);
        }
        // Handle FPS
        const int CURRENT_TIME_MS = SDL_GetTicks();
        int ELAPSED_TIME_MS = CURRENT_TIME_MS - LAST_UPDATE_TIME;
        this->_world.update(std::min(ELAPSED_TIME_MS, MAX_FRAME_TIME));
        LAST_UPDATE_TIME = CURRENT_TIME_MS;

        this->draw(graphics);
    }
}

void Game::draw(Graphics &graphics){
    graphics.clear();
    graphics.setColor(255, 255, 255);
    this->_world.draw(graphics);
    graphics.setColor(0, 0, 0);
    graphics.render();
}
