import pygame

pygame.init()
pygame.display.set_caption("Battalion!")
game_running = True
screen = pygame.display.set_mode((640, 240))

update_screen = True
bkg_r = 128
ball = pygame.image.load("ball.gif")
rect = ball.get_rect()
while game_running:
    for event in pygame.event.get():
        # print(event)
        if event.type == pygame.QUIT:
            game_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                if bkg_r != 0:
                    bkg_r -= 1
                    update_screen = True
            elif event.key == pygame.K_l:
                if bkg_r != 255:
                    bkg_r += 1
                    update_screen = True

    if update_screen:
        screen.fill((bkg_r, 128, 128))
        print(pygame.display.get_caption())
#pygame.display.set_caption("Battalion!", "Battalion")
        pygame.draw.rect(screen, (255,0,0), rect, 1)
        screen.blit(ball, rect)
        pygame.draw.rect(screen, (80, 0, 80), (350, 20, 120, 100), 8)
        pygame.display.update()
        update_screen = False
pygame.quit()
