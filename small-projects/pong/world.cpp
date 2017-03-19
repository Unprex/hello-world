#include "world.h"

#include "graphics.h"
#include "globals.h"

World::World(){
    this->_multiplayer = this->_running = true;
    this->_dp1 = this->_dp2 = 0;
    this->_pp1 = this->_pp2 = globals::SCREEN_HEIGHT / 2;
    this->_paddleSize = 32;
    this->_game = this->_scoreP1 = this->_scoreP2 = 0;
    this->startGame();
}

void World::startGame(){
    this->_running = !this->_running;
    if(this->_running){
        this->_game++;
        this->_ballX = globals::SCREEN_WIDTH / 2;
        this->_ballY = globals::SCREEN_HEIGHT / 2;
        this->_ballDx = this->_game % 2 == 0;
        this->_ballDy = this->_game % 4 > 1;
    }
}
void World::changeGameMode(){
    if(!this->_running){
        this->_multiplayer = !this->_multiplayer;
        this->_scoreP1 = this->_scoreP2 = 0;
    }
}
void World::changeDifficulty(){
    if(!this->_running){
        this->_paddleSize *= 2;
        if(this->_paddleSize > 64) this->_paddleSize = 4;
    }
}

void World::moveP1(unsigned char m){
    this->_dp1 = m - 1;
}
void World::moveP2(unsigned char m){
    if(this->_multiplayer) this->_dp2 = m - 1;
}

void World::update(int elapsedTime){
    elapsedTime *= globals::SPEED;
    // P1
    this->_pp1 += this->_dp1 * elapsedTime;
    while(this->_pp1 < this->_paddleSize) this->_pp1++;
    while(this->_pp1 > globals::SCREEN_HEIGHT-this->_paddleSize) this->_pp1--;
    // P2
    if(this->_multiplayer){
        this->_pp2 += this->_dp2 * elapsedTime;
        while(this->_pp2 < this->_paddleSize) this->_pp2++;
        while(this->_pp2>globals::SCREEN_HEIGHT-this->_paddleSize) this->_pp2--;
    }
    // Ball
    if(this->_running){
        this->_ballX += (this->_ballDx ? 0.4 : -0.4) * elapsedTime;
        this->_ballY += (this->_ballDy ? 0.4 : -0.4) * elapsedTime;
        if(this->_ballY < 8) this->_ballDy = true;
        if(this->_ballX < 68 && this->_ballX > 60 &&
           this->_ballY < this->_pp1+this->_paddleSize &&
           this->_ballY > this->_pp1-this->_paddleSize){
            this->_ballDx = true;
            if(!this->_multiplayer) this->_scoreP1++;
        }
        if(this->_ballY > globals::SCREEN_HEIGHT-8) this->_ballDy = false;
        if(this->_multiplayer && this->_ballX > globals::SCREEN_WIDTH-68 &&
           this->_ballX < globals::SCREEN_WIDTH-60 &&
           this->_ballY < this->_pp2+this->_paddleSize &&
           this->_ballY > this->_pp2-this->_paddleSize) this->_ballDx = false;
        else if(!this->_multiplayer && this->_ballX > globals::SCREEN_WIDTH-68)
            this->_ballDx = false;
        if(this->_ballX < 0){
            this->_scoreP2++;
            this->startGame();
        }
        if(this->_ballX > globals::SCREEN_WIDTH){
            this->_scoreP1++;
            this->startGame();
        }
    }
}

void World::draw(Graphics &graphics){
    // Center line
    graphics.drawLine(globals::SCREEN_WIDTH/2, 0, globals::SCREEN_WIDTH/2,
                      globals::SCREEN_HEIGHT, 2);
    // Borders
    graphics.drawLine(4, 0, 4, globals::SCREEN_HEIGHT, 8);
    graphics.drawLine(4, globals::SCREEN_HEIGHT-4, globals::SCREEN_WIDTH-4,
                      globals::SCREEN_HEIGHT-4, 8);
    graphics.drawLine(4, 4, globals::SCREEN_WIDTH-4, 4, 8);
    graphics.drawLine(globals::SCREEN_WIDTH-4, 0, globals::SCREEN_WIDTH-4,
                      globals::SCREEN_HEIGHT, 8);
    // P1
    graphics.drawLine(64, this->_pp1+this->_paddleSize, 64,
                      this->_pp1-this->_paddleSize, 8);
    // P2
    if(this->_multiplayer){
        graphics.drawLine(globals::SCREEN_WIDTH-64,
                          this->_pp2+this->_paddleSize,
                          globals::SCREEN_WIDTH-64,
                          this->_pp2-this->_paddleSize, 8);
    }else{
        graphics.drawLine(globals::SCREEN_WIDTH-64, 0,
                          globals::SCREEN_WIDTH-64, globals::SCREEN_HEIGHT, 8);
    }
    // Ball
    if(this->_running) graphics.drawLine(this->_ballX - 4, this->_ballY,
                                         this->_ballX + 4, this->_ballY, 8);
    // Score P1
    for(unsigned int i(0); i < this->_scoreP1; i++){
        graphics.drawLine(globals::SCREEN_WIDTH/2 - 32 - 8 * i, 30,
                          globals::SCREEN_WIDTH/2 - 32 - 8 * i, 34, 4);
    }
    // Score P2
    for(unsigned int i(0); i < this->_scoreP2; i++){
        graphics.drawLine(globals::SCREEN_WIDTH/2 + 32 + 8 * i, 30,
                          globals::SCREEN_WIDTH/2 + 32 + 8 * i, 34, 4);
    }
}
