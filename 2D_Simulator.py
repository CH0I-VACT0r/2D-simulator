import pygame
import math
import time

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# 폰트 초기화
font = pygame.font.Font(None, 36)

# 물리 상수
gravity = 0.5
friction = 0.99
drag_coefficient = 0.01

class Part:
    def __init__(self, x, y, radius, mass):
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = mass
        self.vel_x = 0
        self.vel_y = 0
        self.angle = 0
        self.angular_velocity = 0
        self.dragging = False
        self.trail = []  # 이동 궤적
        self.trail_time = []  # 각 점의 시간 기록
        self.top_x = x  # 맨 위 점의 x 좌표
        self.top_y = y - radius  # 맨 위 점의 y 좌표

    def apply_gravity(self, slope_angle):
        # 중력 가속도 계산
        gravity_x = gravity * math.sin(math.radians(slope_angle))
        gravity_y = gravity * math.cos(math.radians(slope_angle))
        self.vel_x += gravity_x
        self.vel_y += gravity_y

        # 중력으로 인한 회전 토크 계산
        parallel_force = self.mass * gravity * math.sin(math.radians(slope_angle))
        torque = parallel_force * self.radius
        inertia = 0.5 * self.mass * self.radius ** 2
        self.angular_velocity += torque / inertia

    def move(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.update_top_point()  # 맨 위 점 위치 갱신

    def apply_friction(self):
        self.vel_x *= friction
        self.vel_y *= friction
        self.angular_velocity *= 0.99

    def apply_air_resistance(self):
        self.vel_x -= drag_coefficient * self.vel_x
        self.vel_y -= drag_coefficient * self.vel_y

    def apply_impulse(self, force_x, force_y, torque):
        self.vel_x += force_x / self.mass
        self.vel_y += force_y / self.mass
        inertia = 0.5 * self.mass * self.radius ** 2
        self.angular_velocity += torque / inertia

    def update_rotation(self):
        self.angle += self.angular_velocity
        self.angular_velocity *= 0.995

    def update_top_point(self):
        #원의 회전 각도에 따라 맨 위 점의 위치를 갱신
        self.top_x = self.x + self.radius * math.sin(math.radians(self.angle))
        self.top_y = self.y - self.radius * math.cos(math.radians(self.angle))

    def draw(self, screen):
        # 궤적에 추가
        current_time = time.time()
        self.trail.append((self.top_x, self.top_y))
        self.trail_time.append(current_time)

        # 지나간 궤적 제거
        self.trail = [(x, y) for (x, y), t in zip(self.trail, self.trail_time) if current_time - t <= 2]
        self.trail_time = [t for t in self.trail_time if current_time - t <= 2]

        # 궤적 표시
        for point in self.trail:
            pygame.draw.circle(screen, (255, 0, 0), (int(point[0]), int(point[1])), 3)  # 빨간색 점으로 표시

        # 원 그리기
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (0, 0, 255), (int(self.top_x), int(self.top_y)), 5)

    def check_boundary_collision(self, width, height):
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vel_x = -self.vel_x
        elif self.x + self.radius > width:
            self.x = width - self.radius
            self.vel_x = -self.vel_x

        if self.y - self.radius < 0:
            self.y = self.radius
            self.vel_y = -self.vel_y
        elif self.y + self.radius > height:
            self.y = height - self.radius
            self.vel_y = -self.vel_y

    def check_mouse_collision(self, mouse_pos):
        distance = math.sqrt((mouse_pos[0] - self.x) ** 2 + (mouse_pos[1] - self.y) ** 2)
        return distance <= self.radius

class Ground:
    def __init__(self, y):
        self.base_y = y
        self.angle = 0

    def calculate_points(self):
        x1, x2 = 0, 800
        y1 = self.base_y - math.tan(math.radians(self.angle)) * 400
        y2 = self.base_y + math.tan(math.radians(self.angle)) * 400
        return [(x1, y1), (x2, y2)]

    def draw(self, screen):
        points = self.calculate_points()
        pygame.draw.line(screen, (0, 0, 0), points[0], points[1], 2)

    def update_angle(self, direction):
        if direction == 'up' and self.angle < 30:
            self.angle += 5
        elif direction == 'down' and self.angle > -30:
            self.angle -= 5

def check_ground_collision(part, ground):
    part_bottom = part.y + part.radius
    ground_points = ground.calculate_points()
    ground_height = ground_points[0][1] + (part.x / 800) * (ground_points[1][1] - ground_points[0][1])
    if part_bottom >= ground_height:
        part.vel_y = -abs(part.vel_y) * 0.8
        part.y = ground_height - part.radius
        part.vel_x *= friction

head = Part(400, 300, 20, 1)
ground = Ground(400)

running = True
impulse_strength = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                ground.update_angle('up')
            elif event.key == pygame.K_a:
                ground.update_angle('down')
            elif event.key == pygame.K_SPACE:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = head.x - mouse_x
                dy = head.y - mouse_y
                distance = math.sqrt(dx**2 + dy**2)
                if distance > 0:
                    direction_x = dx / distance
                    direction_y = dy / distance
                    max_force = 1000
                    min_force = 1
                    impulse_strength = min_force + (max_force / max(distance, 5))
                    impulse_strength = max(min_force, min(impulse_strength, max_force))
                    force_x = direction_x * impulse_strength
                    force_y = direction_y * impulse_strength
                    torque = head.radius * impulse_strength
                    head.apply_impulse(force_x, force_y, torque)

        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                drag_coefficient = min(drag_coefficient + 0.01, 0.5)
            elif event.y < 0:
                drag_coefficient = max(drag_coefficient - 0.01, 0.01)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if head.check_mouse_collision(event.pos):
                    head.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                head.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if head.dragging:
                head.x, head.y = event.pos

    slope_angle = ground.angle
    if not head.dragging:
        head.apply_gravity(slope_angle)
        head.apply_air_resistance()
        head.move()
        head.apply_friction()
        head.update_rotation()
        head.check_boundary_collision(800, 600)

    check_ground_collision(head, ground)

    screen.fill((255, 255, 255))
    ground.draw(screen)
    head.draw(screen)

    drag_text = font.render(f"Resistance: {drag_coefficient:.2f}", True, (0, 0, 0))
    screen.blit(drag_text, (10, 10))
    impulse_text = font.render(f"Impulse: {impulse_strength:.2f}", True, (0, 0, 0))
    screen.blit(impulse_text, (10, 50))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()