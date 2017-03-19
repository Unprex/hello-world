#include "graphics.h"

#include "globals.h"

Graphics::Graphics(){
    this->_window = SDL_CreateWindow("Pong", SDL_WINDOWPOS_CENTERED,
                                     SDL_WINDOWPOS_CENTERED,
                                     globals::SCREEN_WIDTH,
                                     globals::SCREEN_HEIGHT,
                                     SDL_WINDOW_OPENGL|SDL_WINDOW_RESIZABLE);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8);
    SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8);
    SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8);
    SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 8);
    this->_context = SDL_GL_CreateContext(this->_window);
    SDL_GL_SetSwapInterval(1);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    glOrtho(0, globals::SCREEN_WIDTH, globals::SCREEN_HEIGHT, 0, -1, 1);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glEnable(GL_BLEND);
    glClearColor(0.0, 0.0, 0.0, 1.0);
}

Graphics::~Graphics(){
    SDL_GL_DeleteContext(this->_context);
    SDL_DestroyWindow(this->_window);
}

void Graphics::setColor(unsigned char r, unsigned char g, unsigned char b){
    glColor4f(r/255.0, g/255.0, b/255.0, 1.0);
}

void Graphics::drawLine(double x1, double y1, double x2, double y2, int lSize){
    glLineWidth(lSize * globals::SPRITE_SCALE);
    x1 = x1 * globals::SPRITE_SCALE;
    y1 = y1 * globals::SPRITE_SCALE;
    x2 = x2 * globals::SPRITE_SCALE;
    y2 = y2 * globals::SPRITE_SCALE;
    glBegin(GL_LINES);
    glVertex2f(x1, y1);
    glVertex2f(x2, y2);
    glEnd();
}

void Graphics::render(){
    SDL_GL_SwapWindow(this->_window);
}

void Graphics::clear(){
    glClear(GL_COLOR_BUFFER_BIT);
}
