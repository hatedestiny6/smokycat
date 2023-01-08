import os
import random
import sys

import pygame

import data.modules.config
from data.modules.animated_smoky import AnimatedSmoky
from data.modules.background import Background
from data.modules.barrier import Barrier
from data.modules.config import FIRST_LIFE_SHIFT, FPS, WIDTH, \
    HEIGHT, BG_SPEED, BG_SPEED_PLUS, BG_TIMER_SECONDS, BARRIER_TIMER_SECONDS, \
    BARRIER_TIMER_DELAY, BARRIER_X, JUMP_COUNT, COLLIDE_MILLIS, COLLIDE_LOOPS, \
    BARRIER_SIZE_X, COUNT_TEXT_X, COUNT_TEXT_Y
from data.modules.lives import Life, Lives
from data.modules.menu import Menu
from data.modules.point import Point
from data.modules.database import DataBase


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname).convert_alpha()
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message) from message

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


# функция прыжка
def jump():
    global is_jump, jump_count, smoky

    # если перемещение в пределах разумного
    if jump_count >= -30:
        # в класс героя добавлена функция move
        # она осуществляет перемещение героя
        # по переданным координатам
        # res_x + x
        # res_y + y
        # res_x = итоговый x
        # res_y = итоговый y
        # x, y - аргументы "сдвига"
        smoky.move(0, -jump_count / 2.5)
        jump_count -= 1

    else:
        # возвращаем исходные значения
        jump_count = 30
        is_jump = False


def terminate():
    pygame.quit()
    sys.exit()


def end():
    size = (WIDTH, HEIGHT)
    end_group = pygame.sprite.Group()

    over_image = pygame.transform.scale(load_image("images/game_over/gameover.png"), (1200, 720))
    over = pygame.sprite.Sprite(end_group)
    over.image = over_image
    over.rect = over.image.get_rect()
    over.rect.topleft = (-1200, 0)

    running = True
    v = 1000
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type in [pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN] and over.rect.bottomright >= size:
                return

        screen.fill(pygame.Color("black"))
        end_group.draw(screen)
        if over.rect.bottomright < size:
            over.rect.left += v / FPS

        clock.tick(FPS)
        pygame.display.flip()

    pygame.quit()


def show_result():
    FPS = 20

    # выбираем правильную форму слова "рыбки" в зависимости от результата
    if (count_fish % 10) == 0 or (5 <= (count_fish % 10) <= 9) or count_fish == 11:
        result = font.render(f"Вы собрали {count_fish} рыбок!", True, (255, 192, 203))
    elif (count_fish % 10) == 1:
        result = font.render(f"Вы собрали {count_fish} рыбку!", True, (255, 192, 203))
    else:
        result = font.render(f"Вы собрали {count_fish} рыбки!", True, (255, 192, 203))

    result_x = 390
    result_y = 200

    press_any = font.render("Нажмите любую клавишу для продолжения", True, (255, 255, 255))
    pa_x = 160
    pa_y = 300

    smoky_sprite = pygame.sprite.Group()
    _ = AnimatedSmoky(smoky_sprite, load_image("images/right/smoky_right_sheet.png"), 3, 1, 530, 495)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type in [pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN]:
                base.update_balance(count_fish)
                base.terminate()
                pygame.quit()
                return

        screen.fill(pygame.Color("black"))

        screen.blit(result, (result_x, result_y))
        screen.blit(press_any, (pa_x, pa_y))
        smoky_sprite.draw(screen)
        smoky_sprite.update()

        clock.tick(FPS)
        pygame.display.flip()

    pygame.quit()


def start_screen():
    global clock, smoky, is_jump, jump_count, screen, font, base

    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Smoky Cat")
    clock = pygame.time.Clock()
    # база данных
    base = DataBase()
    # FONTS
    font, font_head, font_balance = data.modules.config.get_fonts()
    # заголовок
    head = font_head.render("Smoky Cat", True, (255, 255, 255))
    # баланс
    balance = font_balance.render(f"Баланс: {base.get_balance()}", True, (138, 43, 226))
    # меню
    menu = Menu()
    menu.append_option('Играть', lambda: 1)
    menu.append_option('Выйти', terminate)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if pygame.key.get_pressed()[pygame.K_UP]:
                menu.switch(-1)

            if pygame.key.get_pressed()[pygame.K_DOWN]:
                menu.switch(1)

            if pygame.key.get_pressed()[pygame.K_RETURN]:
                # если игрок нажал кнопку "Играть"
                if menu.current_option_index == 0:
                    return  # начинаем игру

                menu.select()

        screen.fill((0, 0, 0))

        menu.draw(screen, 550, 350, 75)
        screen.blit(head, (420, 120))
        screen.blit(balance, (20, 0))

        pygame.display.flip()
        clock.tick(FPS)


def game():
    global jump_count, smoky, count_fish, is_collide, is_jump, \
        barrier_timer_seconds, fps

    # общие
    fps = FPS
    # каждые BG_TIMER_SECONDS секунд
    # увеличиваем скорость движения фона
    # на BG_SPEED_PLUS пикселей
    speed_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(speed_timer, BG_TIMER_SECONDS)
    # событие переключения анимации героя
    anim_event = pygame.USEREVENT + 3
    pygame.time.set_timer(anim_event, 100)

    # тексты
    # счетчик рыбок
    count_fish = 0
    count_text = font.render(f"Рыбки: {count_fish}", True, (255, 192, 203))
    screen.blit(count_text, (COUNT_TEXT_X, COUNT_TEXT_Y))

    # Группа спрайтов фона
    # сюда относятся два фона
    # и камни, т.к. они движутся синхронно с фонами
    bg_group = pygame.sprite.Group()
    # группа спрайтов для героя
    smoky_sprite = pygame.sprite.Group()

    # определяем 2 фона
    # первый - основной, его видит игрок
    # второй - за пределами экрана
    # нужен для иллюзии бесконечного мира
    background1 = Background(bg_group, 0, 0)
    background2 = Background(bg_group, 1270, 0)
    # скорость передвижения фона
    bg_speed = BG_SPEED

    # инициализируем камни (препятствия)
    # начальная координата любого камня
    barrier_x = BARRIER_X
    # изначально камни будут появляться каждые BARRIER_TIMER_SECONDS секунд
    barrier_timer_seconds = BARRIER_TIMER_SECONDS
    # интервал появления камней
    barrier_timer = pygame.USEREVENT + 2
    pygame.time.set_timer(barrier_timer, barrier_timer_seconds)
    # список всех существующих камней
    barriers_in_game = [Barrier(bg_group, barrier_x)]

    # создаем очки (рыбки)
    # интервал появления тот же, что и для камней
    # список всех существующих монеток
    points_in_game = []

    # Характеристики прыжка
    # флаг
    is_jump = False
    # счетчик прыжков
    jump_count = JUMP_COUNT

    # Жизни
    # таймер
    # Когда персонаж сталкивается, имитируем столкновение.
    # Для этого будем заставлять персонажа "мигать" 4 раза.
    # Для реализации "мигания" и нужен этот таймер.
    # "Мигание":
    #           * если спрайт скрыт, ждём 200 миллисекунд и показываем
    #           * если спрайт показан, ждём 200 миллисекунд и скрываем
    collide_timer = pygame.USEREVENT + 4
    # было ли столкновение
    is_collide = False
    # событие, которое возвращает исходные параметры
    # игры после завершения столкновения
    reset_event = pygame.USEREVENT + 5

    # новая жизнь
    life = Life(FIRST_LIFE_SHIFT)
    # все жизни
    lives = Lives(life)

    # главный герой
    smoky = AnimatedSmoky(smoky_sprite, load_image("images/right/smoky_right_sheet.png"), 3, 1, 200, 495)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # переключаем фрейм
            if event.type == anim_event:
                smoky_sprite.update()

            # если игрок нажал пробел и прыжок неактивен
            # активируем прыжок
            if not is_jump and pygame.key.get_pressed()[pygame.K_SPACE]:
                is_jump = True

            # если пришло время создавать камень
            # или рыбку
            if event.type == barrier_timer:
                # создаем камень
                # добавляем его в список существующих
                # переопределяем координату камня
                # делаем ее случайной для разнообразия позиций камней
                barrier_x = random.randint(BARRIER_X, BARRIER_X + 200)
                barriers_in_game.append(Barrier(bg_group, barrier_x))
                # то же самое для рыбки
                # начальная координата
                # + 10 нужно, чтобы рыбка в случае выбора random-ом число, стоящее
                # 1 аргументом, не прилипла к камню
                point_x = random.randint(barrier_x + BARRIER_SIZE_X + 10, barrier_x + random.randint(250, 450))

                # # здесь нужно проверить
                # # чтобы новая рыбка не пересекалась
                # # ни с одним из камней
                # # тк это дефект
                # if barriers_in_game:
                #     for barrier in barriers_in_game:
                #         # если рыбка пересекается с одним из камней
                #         while pygame.sprite.collide_mask(Point(bg_group, point_x), barrier):
                #             # переопределяем координату
                #             point_x = random.randint(barrier_x, barrier_x + random.randint(450, 600))

                # добавляем рыбку
                points_in_game.append(Point(bg_group, point_x))

            # анимация мигания при столкновении
            if event.type == collide_timer:
                # если нужно скрыть
                # то есть если персонаж есть на экране
                if smoky_sprite:
                    smoky.kill()
                else:
                    # возвращаем персонажа обратно на экран
                    smoky_sprite.add(smoky)

            # возвращаем исходные значения
            if event.type == reset_event:
                # столкновение прошло
                is_collide = False
                # возвращаем исходные значения
                bg_speed *= 2

            # ускорение каждые 10 секунд
            if event.type == speed_timer:
                # ускоряем движение
                bg_speed += BG_SPEED_PLUS
                # камни появляются чаще
                barrier_timer_seconds -= BARRIER_TIMER_DELAY
                # ставим новый таймер для камней
                pygame.time.set_timer(barrier_timer, barrier_timer_seconds)
                # делаем плавнее чтобы персонаж
                # прыгал быстрее
                fps += 4

        screen.fill(pygame.Color("black"))

        # отображаем все
        bg_group.draw(screen)
        smoky_sprite.draw(screen)
        lives.draw(screen)
        screen.blit(count_text, (COUNT_TEXT_X, COUNT_TEXT_Y))

        # Сдвиг фона и камня
        # он одинаковый, т.к. камень должен
        # передвигаться параллельно с фоном
        # чтобы игрок видел камень
        # который стоит на месте
        shift = bg_speed / fps

        if is_jump:
            jump()  # осуществляет прыжок

        # если камни существуют
        if barriers_in_game:
            # Пробегаемся по всем камням
            # здесь нужно использовать цикл while,
            # т.к. мы удаляем элементы из списка, или
            # проводим очистку списка от камней за пределами
            # экрана
            index = 0
            while index < len(barriers_in_game):
                barrier = barriers_in_game[index]
                if barrier.rect.topright[0] < 0:
                    barriers_in_game.remove(barrier)
                    bg_group.remove(barrier)
                    continue
                # если какой-нибудь камень и игрок пересеклись
                # и если столкновения еще не было
                if barrier.check(smoky) and not is_collide:
                    # делаем последнюю жизнь неактивной
                    # меняем ее изображение на image_inactive
                    lives.last_life().image = Life.image_inactive

                    # если все жизни утрачены
                    if not lives.items:
                        end()  # показываем картинку Game Over
                        show_result()  # показываем результат игры
                        # запускаем программу с самого начала
                        pygame.quit()
                        return "Continue"

                    # столкновение было
                    is_collide = True
                    # замедляем фон
                    bg_speed //= 2
                    # пересчитываем сдвиг во избежание разрыва синхронности между
                    # движением фона и камня
                    # иначе игрок увидит, будто персонаж "толкает" камень
                    # в течение доли секунды
                    shift = bg_speed / FPS
                    # ставим таймер
                    # повтор - 4 раза
                    pygame.time.set_timer(collide_timer, COLLIDE_MILLIS, COLLIDE_LOOPS)
                    # нужно задать reset_event
                    pygame.time.set_timer(reset_event, COLLIDE_MILLIS * COLLIDE_LOOPS, 1)
                    # Задаем таймер появления камней заново, чтобы отчет
                    # пошел с нуля.
                    # Это нужно чтобы в момент столкновения камни
                    # не продолжали появляться, иначе их станет
                    # слишком много и игрок не сможет пройти дальше
                    pygame.time.set_timer(barrier_timer, barrier_timer_seconds)
                else:
                    # передвигаем камень наравне с фоном
                    barrier.move(shift)

                # итерация
                index += 1

        # все то же, что и с камнями
        if points_in_game:
            for point in points_in_game:
                # проверка пересечения рыбки и игрока
                if not point.check(smoky, shift):
                    # кол-во рыбок +1
                    count_fish += 1
                    # переопределяем текст с обновлённым балансом
                    count_text = font.render(f"Рыбки: {count_fish}", True, (255, 192, 203))
                    # удаляем элемент из списка
                    points_in_game.remove(point)
                    # удаляем его с экрана
                    point.kill()

        """MOVE BG"""
        # двигаем спрайты
        background1.move(-shift)
        background2.move(-shift)

        # если первый фон вышел за пределы экрана
        # (правый верхний угол < 0)
        # перемещаем его левый верхний угол
        # в точку 1270, 0
        if background1.check():
            background1.move(1270 * 2)
        # так же со вторым
        if background2.check():
            background2.move(1270 * 2)
        """========"""

        clock.tick(fps)
        pygame.display.flip()

    pygame.quit()
    # надо завершить программу
    return False


# после проигрыша программа будет перезапускаться
# с самого начала пока игрок не выйдет сам
do = True
while do:
    start_screen()
    do = game()
