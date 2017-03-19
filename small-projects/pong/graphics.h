#ifndef GRAPHICS_H
#define GRAPHICS_H

#include <SDL2/SDL.h>
#define GLEW_STATIC
#include <GL/glew.h>

class Graphics{
public:
    Graphics();
    ~Graphics();

    void setColor(unsigned char r, unsigned char g, unsigned char b);

    void drawLine(double x1, double y1, double x2, double y2, int lSize);

    void render(); // Renders to the screen.
    void clear(); // Clears the screen.
private:
    SDL_Window* _window;
    SDL_GLContext _context;
};

#endif // GRAPHICS_H
