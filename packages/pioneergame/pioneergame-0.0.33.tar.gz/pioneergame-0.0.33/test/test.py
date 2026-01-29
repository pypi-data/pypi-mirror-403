from pioneergame import Window, Label, Button, Rect, Sprite, explode, explosion_update

window = Window(1050, 900)
fps = 60

test = Sprite(window, '')
test.attach_to(Rect(window, 100, 100, 100, 100))

while True:
    window.fill('black')
    test.draw()
    test.rotate(10)

    window.update(fps)
