#ifndef WORLD_H
#define WORLD_H

class Graphics;

class World{
public:
    World();

    void startGame(); // change paddle size
    void changeGameMode(); // change multi player
    void changeDifficulty(); // change paddle size
    void moveP1(unsigned char m); // 0 : up; 1 : no movement; 2 : down;
    void moveP2(unsigned char m);

    void update(int elapsedTime);
    void draw(Graphics &graphics);
private:
    bool _running, _multiplayer, _ballDx, _ballDy;
    unsigned int _paddleSize, _game, _scoreP1, _scoreP2;
    float _dp1, _dp2, _pp1, _pp2, _ballX, _ballY;

};

#endif // WORLD_H
