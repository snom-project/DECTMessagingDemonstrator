# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
"""Interactive Location Viewer

This module demonstrates Beacon devices moving on a map, detected by M9Bs in TX mode.

Execution:
    run the live location viewer by::

        $ python3 live_location.py

Todo:
    * Clean Up
    * view dimenions conversion from meters to screen coordinates
    * background image
"""
import logging
import localization as lx
import pygame
import numpy as np
from numpy.linalg import inv

from DB.DECTMessagingDb import DECTMessagingDb
from Trilateration import calc_dist


# positions in % of viewport
 # x = 83 px = 4.5m  / = 5.42168675 - 1px in cm / = 18,4444 - 1m in px
    # y = 128 px = 6.5m / = 5.078125 / = 19.6923077 - 1m in px
#x_ratio = 5.42168675
#y_ratio = 5.078125


#84x84 pixel entspricht 1x1 m
x_ratio = 100.0 / 84.0 
y_ratio = 100.0 / 84.0


# Feuerstrecke
offset6OG = (475.0 * x_ratio, 0 * y_ratio)

offsetOG = (475.0, 0)

m9bpositions = [
    # UG
    {'m9b_IPEI': '0328D7830E','x': (91.0 + 84.0*0.0 + 42.0) * x_ratio, 'y':118.0 * y_ratio, 'z':0.0},
    {'m9b_IPEI': '0328D3C918','x': (91.0 + 84.0*2.0 + 42.0) * x_ratio, 'y':118.0 * y_ratio, 'z':0.0},

    {'m9b_IPEI': '0328D3C922','x': (91.0 + 84.0*0.0 + 42.0) * x_ratio, 'y':(118.0 + 84.0*1.0) * y_ratio, 'z':0.0},
    {'m9b_IPEI': '0328D3C911','x': (91.0 + 84.0*2.0 + 42.0) * x_ratio, 'y':(118.0 + 84.0*1.0) * y_ratio, 'z':0.0},
  
    {'m9b_IPEI': '0328D3C921','x': (91.0 + 84.0*3.0) * x_ratio, 'y':(118.0 + 84.0*2.0 - 42.0) * y_ratio, 'z':0.0},
    {'m9b_IPEI': '0328D3C921','x': (91.0 + 84.0*4.0) * x_ratio, 'y':(118.0 + 84.0*2.0 - 42.0) * y_ratio, 'z':0.0},
   
    {'m9b_IPEI': '0328D3C921','x': (91.0 + 84.0*3.0) * x_ratio, 'y':(118.0 + 84.0*4.0 - 42.0) * y_ratio, 'z':0.0},
    {'m9b_IPEI': '0328D3C921','x': (91.0 + 84.0*4.0) * x_ratio, 'y':(118.0 + 84.0*4.0 - 42.0) * y_ratio, 'z':0.0},
  
    {'m9b_IPEI': '0328D3C921','x': (91.0 + 84.0*3.0) * x_ratio, 'y':(118.0 + 84.0*6.0 - 42.0) * y_ratio, 'z':0.0},
    {'m9b_IPEI': '0328D3C921','x': (91.0 + 84.0*4.0) * x_ratio, 'y':(118.0 + 84.0*6.0 - 42.0) * y_ratio, 'z':0.0},
    
    # OG
    {'m9b_IPEI': '0328D78303','x': (91.0 + 84.0*0.0 + 42.0 + offsetOG[0]) * x_ratio, 'y':118.0 * y_ratio, 'z':3.0},
    {'m9b_IPEI': '0328D3C913','x': (91.0 + 84.0*2.0 + 42.0 + offsetOG[0]) * x_ratio, 'y':118.0 * y_ratio, 'z':3.0},

    {'m9b_IPEI': '0328D78303','x': (91.0 + 84.0*0.0 + 42.0 + offsetOG[0]) * x_ratio, 'y':(118.0 + 84.0*1.0) * y_ratio, 'z':3.0},
    {'m9b_IPEI': '0328D3C913','x': (91.0 + 84.0*2.0 + 42.0 + offsetOG[0]) * x_ratio, 'y':(118.0 + 84.0*1.0) * y_ratio, 'z':3.0},
  
    {'m9b_IPEI': '0328D3C923','x': (91.0 + 84.0*3.0 + offsetOG[0]) * x_ratio, 'y':(118.0 + 84.0*2.0 - 42.0) * y_ratio, 'z':3.0},
    {'m9b_IPEI': '0328D3C923','x': (91.0 + 84.0*4.0 + offsetOG[0]) * x_ratio, 'y':(118.0 + 84.0*2.0 - 42.0) * y_ratio, 'z':3.0},
   
    {'m9b_IPEI': '0328D3C923','x': (91.0 + 84.0*3.0 + offsetOG[0]) * x_ratio, 'y':(118.0 + 84.0*4.0 - 42.0) * y_ratio, 'z':3.0},
    {'m9b_IPEI': '0328D3C923','x': (91.0 + 84.0*4.0 + offsetOG[0]) * x_ratio, 'y':(118.0 + 84.0*4.0 - 42.0) * y_ratio, 'z':3.0},
  
    {'m9b_IPEI': '0328D3C923','x': (91.0 + 84.0*3.0 + offsetOG[0]) * x_ratio, 'y':(118.0 + 84.0*6.0 - 42.0) * y_ratio, 'z':3.0},
    {'m9b_IPEI': '0328D3C923','x': (91.0 + 84.0*4.0 + offsetOG[0]) * x_ratio, 'y':(118.0 + 84.0*6.0 - 42.0) * y_ratio, 'z':3.0},
  ]

# Define some colors
BLACK   = (100, 100, 100)
WHITE   = (255, 255, 255)
RED     = (255,   0,   0)
GREEN   = (  0, 255,   0)
BLUE    = ( 20,  20, 255)
YELLOW  = (255, 205,   0)
CYAN    = (  0, 255, 255)
PURPLE  = (255,   0, 255)

colors = [RED, GREEN, BLUE, PURPLE, CYAN]

class Text(pygame.sprite.Sprite):
    def __init__(self, text, size, color, width, height):
        # Call the parent class (Sprite) constructor  
        pygame.sprite.Sprite.__init__(self)

        self.font = pygame.font.SysFont("Arial", size)
        self.textSurf = self.font.render(text, 1, color)
        self.W = self.textSurf.get_width()
        self.H = self.textSurf.get_height()


class Active_Area(pygame.sprite.Sprite):
    """
    This class represents the active area of the floorplan.
    """
    def __init__(self):
        """ Constructor. Pass in the color of the block,
        and its size. """

        # Call the parent class (Sprite) constructor
        super().__init__()

        # load an alpha image as floorplan mask        
        self.image = pygame.image.load("./alpha.png").convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()


class M9B(pygame.sprite.Sprite):
    """
    This class represents M9B or device.
    """

    def __init__(self, color, width, height, name='UNKNOWN'):
        """ Constructor. Pass in the color of the block,
        and its size. """

        # Call the parent class (Sprite) constructor
        super().__init__()

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.image = pygame.Surface([width, height])
        #self.image.fill(color)
        #self.image.set_colorkey((255, 255, 255))
        
        man_image = pygame.image.load("./beacon-icon-21.jpg").convert()
        #man_imaget.set_colorkey((255, 255, 255))
        #man_image = pygame.transform.smoothscale(man_imaget, (width, height))
        #man_image.set_colorkey(WHITE)

        self.image.blit(man_image, [0, 0])

        #self.image.fill(color)
        self.color = color
        self.name = name
        
        self.rect = self.image.get_rect()

        self.txt_surf = Text(self.name[-4:], 11, RED, 50, 50)

        self.image.blit(self.txt_surf.textSurf, 
                        [width/2- self.txt_surf.W/2, height-self.txt_surf.H])
        
    def hover(self, hover=False):
        """prints M9B Info
        """   
        if hover:
            self.image.fill(YELLOW)
        else:
            self.image.fill(self.color)

#txt = Text('Hello', 20, RED, 50, 100)


class Device(pygame.sprite.Sprite):
    """
    This class represents M9B or device.
    """

    def __init__(self, color, width, height, name='UNKNOWN'):
        """ Constructor. Pass in the color of the block,
        and its size. """

        # Call the parent class (Sprite) constructor
        super().__init__()

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        #self.image.set_colorkey((255, 255, 255))
        
        man_image = pygame.image.load("./icon-person_black.png").convert()
        #man_imaget.set_colorkey((255, 255, 255))
        #man_image = pygame.transform.smoothscale(man_imaget, (width, height))
        man_image.set_colorkey(WHITE)

        self.image.blit(man_image, [0, 0])

        #self.image.fill(color)
        self.color = color
        self.name = name
        # Fetch the rectangle object that has the dimensions of the image
        # image.
        # Update the position of this object by setting the values
        # of rect.x and rect.y
        self.rect = self.image.get_rect()
    
    def hover(self, hover=False):
        """prints M9B Info
        """   
        if hover:
            self.image.fill(YELLOW)
        else:
            self.image.fill(self.color)

#txt = Text('Hello', 20, RED, 50, 100)

class RssiArea(pygame.sprite.Sprite):
    ''' M9B Object with RSSI rings animation. '''
    def __init__(self, color, radius):
        # Call the parent class (Sprite) constructor
        super().__init__()

        self.sprites = []

        # let it spring in 5 steps percentage of radius
        for spring_percent in (100,98,97,96,96,97,98,100):
        #for spring_percent in (100,100,100,100,100):
            # Pass in the color of the player, and its x and y position, width and height.
            # Set the background color and set it to be transparent
            self.image = pygame.Surface([radius*2, radius*2])
            self.image.fill(WHITE)
            self.image.set_colorkey(WHITE)

            #Initialise attributes of the car.
            self.color = color
            self.radius = radius

            # Draw the rssi circle
            pygame.draw.circle(self.image, self.color, (self.radius, self.radius),
                               int(self.radius*spring_percent/100.0), width=int(10))
            #pygame.draw.line(self.image, RED, (self.radius, self.radius), (self.radius+50,self.radius))  # Start at topleft and ends at bottomright.
            self.image.set_alpha(50) 

            self.sprites.append(self.image)

        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.center = (0.0, 0.0)
        self.is_animating = False

    def animate(self):
        ''' Turn on sprite animation '''
        self.is_animating = True

    def update(self, step):
        ''' cycle through sprite images to animate '''
        if self.is_animating:
            self.current_sprite += step

            if self.current_sprite >= len(self.sprites):
                self.current_sprite = 0.0
                #self.is_animating = False

            self.image = self.sprites[int(self.current_sprite)]
        
        height = FONT.get_height()
        # Put the rendered text surfaces into this list.
        text_surfaces = []
        (r, _unused, _unused) = toObjectCoordinates(self.radius, 0,0)
        r /= 100.0
        #r = self.radius
        for txt in ('dist',
                    '{:3.1f}'.format(r)):
            text_surfaces.append(FONT.render(txt, True, BLUE))
        # The width of the widest surface.
        #width = max(txt_surf.get_width() for txt_surf in text_surfaces)

        # A transparent surface onto which we blit the text surfaces.
        for y_, txt_surf in enumerate(text_surfaces):
            self.image.blit(txt_surf, (15+self.radius, y_*height+self.radius-height))


def create_rssi_circle(xcenter, ycenter, _zcenter, radius, color=BLACK):
    ''' Build a RSSI Circle from xcenter, ycenter, radius, color '''
    global rssi_circle_list

    rssi_circle = RssiArea(color, radius)
    rssi_circle.rect.center = (xcenter, ycenter)
    # add to the list.
    rssi_circle_list.add(rssi_circle)

def sort_m9b_rssi(selected):
    ''' Return the M9B with the nearest rssi from the M9B list '''
    # get the best visible rssi m9b
    # sort in place
    selected.sort(key=lambda item: item.get("rssi"))
    #print('sorted', selected)
    return selected

def get_m9bposition(ipei):
    ''' return the M9B position to matching ipei from m9bpositions list '''
    match = next( (item for item in m9bpositions if item["m9b_IPEI"] == ipei ), None )
    return match

def is_valid_proximity(proximity):
    # proximity can be '1', '2', '3' or for TAGs 'moving', 'holding_still'
    # TAGs cannot be checked if really still there. 
    if proximity == '0':
            return False
    else:
        return True

def update_all_devices():
    '''
        All devices and their corresponding M9Bs are updated.

        DB sample record:
        [{'account': '000413B50038', 'bt_mac': '000413B50038',
        'rssi': '-53', 'uuid': 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF90FF',
        'beacon_type': 'a', 'proximity': '3',
        'beacon_gateway_IPEI': '0328D3C918', 'beacon_gateway_name': 'Schreibtisch',
        'time_stamp': '2020-10-29 10:44:22.489801', 'server_time_stamp': '2020-10-29 09:44:22',
        'timeout': 96945}]

        real location is defined in list m9bpositions, e.g.
        {'m9b_IPEI': '000413666660', 'x': 0.0, 'y':0.0},
    '''
    # kill all previous M9B animations
    global rssi_circle_list
    rssi_circle_list.empty()
    player_list.empty()

    # floorplan alpha mask to check if device is on the floor 
    global floorplan_alpha_mask

    if msgDb:
        result = msgDb.read_m9b_device_status_db()
        #print(result)

        btmacs_non_unique = [ sub['bt_mac'] for sub in result ]
        btmacs_set = set(btmacs_non_unique)
        btmacs = list(btmacs_set)
        #print('btmacs:', btmacs)

        for idx, btmac in enumerate(btmacs):
            # get m9b data for btmac
            selected_items = [{k:d[k] for k in d if k!="a"} for d in result if d.get("bt_mac") == btmac]
            #print('selected_items:' , selected_items)
            # create list of visible m9bs
            gateway_list = []
            for elem in selected_items:
                if is_valid_proximity(elem['proximity']) and get_m9bposition(elem['beacon_gateway_IPEI']):
                    gateway_list.append({'ipei': elem['beacon_gateway_IPEI'],
                                        'proximity': elem['proximity'],
                                        'rssi': elem['rssi']})
            #print('Full list::', gateway_list)

            for m9b in gateway_list:
                #print(m9b, colors[idx % len(colors)])
                # get physical location
                match = get_m9bposition(m9b['ipei'])

                if match:
                    (xcenter, ycenter, zcenter) = toViewport(float(match['x']), float(match['y']), float(match['z']))
                    (radius, _notused, _notused) = toViewport(calc_dist(float(m9b['rssi']), 2) * 100.0, 0.0)
                    create_rssi_circle(xcenter, ycenter, zcenter, radius, colors[idx % len(colors)])

            # BTLE devices
            #print(colors[idx % len(colors)], idx % len(colors))
            btle_device = Device(colors[idx % len(colors)], 32, 32)
            player_list.add(btle_device)

            # how many M9Bs detected the current BTLE device
            num_m9bs_see_device = len(gateway_list)
            if num_m9bs_see_device == 0:
                continue
            # sort M9Bs, no matter how many we got
            m9bs_sorted = sort_m9b_rssi(gateway_list)
            print(f'sorted m9bs [{num_m9bs_see_device}] for {btmac}:{m9bs_sorted}')
            radius1 = radius2 = radius3 = 0
            match_best = get_m9bposition(m9bs_sorted[0]['ipei'])
            if not match_best:
                continue

            if num_m9bs_see_device >= 3:
                # trilaterate with best, 2nd best, 3rd best
                # best
                match_2ndbest = get_m9bposition(m9bs_sorted[1]['ipei'])
                match_3rdbest = get_m9bposition(m9bs_sorted[2]['ipei'])
                # check to be sure, all positions are defined
                if match_best and match_2ndbest and match_3rdbest:
                    # all units in cm
                    (x1, y1, z1) = (float(match_best['x']),    float(match_best['y']),    float(match_best['z']))
                    (x1, y1, z1)  = adjust_floor(x1, y1, z1)
                    (x2, y2, z2) = (float(match_2ndbest['x']), float(match_2ndbest['y']), float(match_2ndbest['z']))
                    (x2, y2, z2)  = adjust_floor(x2, y2, z2)
                    (x3, y3, z3) = (float(match_3rdbest['x']), float(match_3rdbest['y']), float(match_3rdbest['z']))
                    (x3, y3, z3)  = adjust_floor(x3, y3, z3)

                    radius1 = calc_dist(float(m9bs_sorted[0]['rssi']), 2) * 100.0
                    radius2 = calc_dist(float(m9bs_sorted[1]['rssi']), 2) * 100.0
                    radius3 = calc_dist(float(m9bs_sorted[2]['rssi']), 2) * 100.0
                    #radius3 = calc_dist(float(m9bs_sorted[2]['rssi']), 2) * 100.0

                    P=lx.Project(mode='3D',solver='LSE')

                    P.add_anchor('match_best',(x1,y1,z1))
                    P.add_anchor('match_2ndbest',(x2,y2,z2))
                    P.add_anchor('match_3rdbest',(x3,y3,z3))

                    t,_label=P.add_target(ID=btmac)

                    t.add_measure('match_best',    radius1)
                    t.add_measure('match_2ndbest', radius2)
                    t.add_measure('match_3rdbest', radius3)
                    if radius1 <= 100.0: # 1m
                        for extra in range(5):
                            P.add_anchor(f'match_best{extra}',(x1,y1,z1))
                            t.add_measure(f'match_best{extra}', 1.0)
                    P.solve()
                    # split floors back
                    if t.loc.z > 280.0/2.0: # we are in the 2nd floor
                        t.loc.x += offset6OG[0]
                        t.loc.y += offset6OG[1]

                    # go screen coordinates
                    (xcenter, ycenter, zcenter) = toViewport(t.loc.x, t.loc.y, t.loc.z)
            elif num_m9bs_see_device == 2:
                # all units in cm
                radius1 = calc_dist(float(m9bs_sorted[0]['rssi']), 2) * 100.0
                radius2 = calc_dist(float(m9bs_sorted[1]['rssi']), 2) * 100.0

                match_2ndbest = get_m9bposition(m9bs_sorted[1]['ipei'])
                (x1, y1, z1) = (float(match_best['x']),    float(match_best['y']), float(match_best['z']))
                (x1, y1, z1)  = adjust_floor(x1, y1, z1)
                (x2, y2, z2) = (float(match_2ndbest['x']), float(match_2ndbest['y']), float(match_2ndbest['z']))
                (x2, y2, z2)  = adjust_floor(x2, y2, z2)

                P=lx.Project(mode='3D',solver='LSE')
                t,_label=P.add_target(ID=btmac)

                P.add_anchor('match_best',(x1,y1,z1))
                # we are very very near, increase the influence by adding more points.
                if radius1 <= 100.0: # 1m
                    for extra in range(5):
                        P.add_anchor(f'match_best{extra}',(x1,y1,z1))
                        t.add_measure(f'match_best{extra}', 1.0)
                P.add_anchor('match_2ndbest',(x2,y2,z2))

                t.add_measure('match_best',    radius1)
                t.add_measure('match_2ndbest', radius2)

                P.solve()
                # split floors back
                if t.loc.z > 280.0/2.0: # we are in the 2nd floor
                    t.loc.x += offset6OG[0]
                    t.loc.y += offset6OG[1]

                # go screen coordinates
                (xcenter, ycenter, zcenter) = toViewport(t.loc.x, t.loc.y, t.loc.z)
              
            else:
                # only one M9B, assume direction along X+ achses
                # screen coordinates
                # all units in m
                radius1 = calc_dist(float(m9bs_sorted[0]['rssi']), 2) * 100.0

                (xcenter,ycenter,zcenter) = toViewport(float(match_best['x']) + radius1*0.0, 
                                                       float(match_best['y']),
                                                       float(match_best['z']))

            # screen coordinates
            print(f'pos:({xcenter}, {ycenter}, {zcenter})')
            print(f'radi:({radius1} cm, {radius2} cm, {radius3} cm)')
            if floorplan_alpha_mask.mask.get_at((int(max(0,xcenter)),int(max(0,ycenter)))):
                btle_device.rect.center = (xcenter, ycenter)

def viewport_transformation(Xwmin, Xwmax, Ywmin, Ywmax, Xvmin, Xvmax, Yvmin, Yvmax):
    '''
    Viewport transformation
    return viewport transformation matrix VT

    Step1:Translate window to origin 1
            Tx=-Xwmin Ty=-Ywmin

    Step2:Scaling of the window to match its size to the viewport
            Sx=(Xvmax-Xvmin)/(Xwmax-Xwmin)
            Sy=(Yvmax-Yvmin)/(Ywmax-Ywmin)

    Step3:Again translate viewport to its correct position on screen.
            Tx=Xvmin
            Ty=Yvmin

    Above three steps can be represented in matrix form:
            VT=T * S * T1

    T = Translate window to the origin

    S=Scaling of the window to viewport size

    T1=Translating viewport on screen.
    '''
    T = np.array([[1,0,-Xwmin], [0,1,-Ywmin], [0,0,1]])
    Sx=(Xvmax-Xvmin)/(Xwmax-Xwmin)
    Sy=(Yvmax-Yvmin)/(Ywmax-Ywmin)
    S = np.array([[Sx,0,0],[0,Sy,0],[0,0,1]])
    T1 = np.array([[1,0,Xwmin], [0,1,Ywmin], [0,0,1]])
    VT=T.dot(S.dot(T1))
    print(VT)
    return VT

def toViewport(x_coord, y_coord, z_coord=0.0):
    '''
    transform x,y point into screen space.
    return (x,y) = ViewMatrix * [x,y,0]
    '''
    global ViewMatrix
    p = ViewMatrix.dot(np.array([x_coord,y_coord,z_coord]))
    return (p[0],p[1],p[2])

def toObjectCoordinates(x_coord, y_coord, z_coord=0.0):
    '''
    transform x,y point into screen space.
    return (x,y) = ViewMatrix * [x,y,0]
    '''
    global ViewMatrix
    inverse = inv(ViewMatrix)
    p = inverse.dot(np.array([x_coord,y_coord,z_coord]))
    return (p[0],p[1],p[2])

def adjust_floor(x_coord, y_coord, z_coord):
    global offset6OG
    if z_coord > 0.0:
        # 2nd floor - substract y for floors in one image - one over another
        x_coord -= offset6OG[0]
        y_coord -= offset6OG[1]
    return (x_coord, y_coord, z_coord)

if __name__ == "__main__":
    # prepare logger
    logger = logging.getLogger('LiveLocation')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # get access to the DB
    # DB reuse and type
    ODBC_=False
    INITDB_=False
    msgDb = DECTMessagingDb(odbc=ODBC_, initdb=INITDB_)


    # Initialize Pygame
    pygame.init()
    FONT = pygame.font.Font(None, 20)

    # Set the height and width of the screen
    #image size 1000x748
    SCREEN_WIDTH = int(1000 * 1.0)
    SCREEN_HEIGHT = int(748 * 1.0)
    OBJECT_SPACE_WIDTH = SCREEN_WIDTH*x_ratio
    OBJECT_SPACE_HEIGHT = SCREEN_HEIGHT*y_ratio

    # x = 83 px = 4.5m  / = 5.42168675 - 1px in cm / = 18,4444 - 1m in px
    # y = 128 px = 6.5m / = 5.078125 / = 19.6923077 - 1m in px

    ViewMatrix = viewport_transformation(0.0, OBJECT_SPACE_WIDTH, 0.0, OBJECT_SPACE_HEIGHT, 0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)

    flags = pygame.RESIZABLE
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)

    # this is the alpha channel active area of the floorplan
    floorplan_alpha_mask = Active_Area()
    # This is a list of 'sprites.' Each block in the program is
    # added to this list. The list is managed by a class called 'Group.'
    block_list = pygame.sprite.Group()

    # This is a list of every sprite.
    # All blocks and the player block as well.
    m9b_sprites_list = pygame.sprite.Group()

    for i in range(len(m9bpositions)):
        # This represents a block
        block = M9B(BLUE, 25, 40, m9bpositions[i % len(m9bpositions)]['m9b_IPEI'])

        (x,y,_notused)= toViewport( float(m9bpositions[i % len(m9bpositions)]['x']),
                                    float(m9bpositions[i % len(m9bpositions)]['y']),
                                    float(m9bpositions[i % len(m9bpositions)]['z']))
        block.rect.center = (x,y)
        print(float(m9bpositions[i % len(m9bpositions)]['x']))
        print(block.rect)

        # Add the block to the list of objects
        block_list.add(block)
        m9b_sprites_list.add(block)

    rssi_circle_list = pygame.sprite.Group()
    player_list = pygame.sprite.Group()

    # Create a RED player block
    player = M9B(RED, 20, 15)
    player_list.add(player)

    # Loop until the user clicks the close button.
    done = False

    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()

    background_surfacet = pygame.image.load("./Streckenplan_V2.png")
    background_surface = pygame.transform.smoothscale(background_surfacet, (SCREEN_WIDTH, SCREEN_HEIGHT))

    print(background_surface.get_rect())

    # -------- Main Program Loop -----------
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                for circ in rssi_circle_list:
                    circ.animate()

        # Clear the screen
        #screen.fill(WHITE)
        screen.blit(background_surface, (0, 0))

        # Get the current mouse position. This returns the position
        # as a list of two numbers.
        pos = pygame.mouse.get_pos()

        # Fetch the x and y out of the list,
        # just like we'd fetch letters out of a string.
        # Set the player object to the mouse location
        #player.rect.x = pos[0]
        #player.rect.y = pos[1]

        '''
        for block in block_list:
            if block.rect.collidepoint(pygame.mouse.get_pos()):
                block.hover(True)
            else:
                block.hover(False)
        '''

        # See if the player block has collided with anything.
        #blocks_hit_list = pygame.sprite.spritecollide(player, block_list, False)

        # Check the list of collisions.
        #for block in blocks_hit_list:
        #    print('HIT')
        # Draw all the spites
        m9b_sprites_list.draw(screen)
        player_list.draw(screen)

        # rssi animation will be created from the M9Bs seeing the BTLE beacon
        rssi_circle_list.draw(screen)
        rssi_circle_list.update(0.15)


        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Limit to 60 frames per second
        clock.tick(60)

        #print(pygame.time.get_ticks())

        # update rougly all 2s... the loop can sometimes execute below 20ms ..
        if (pygame.time.get_ticks() % 2000) < 20 :
            update_all_devices()
            #print(pygame.time.get_ticks())
            # new objects need to be animated
            for circ in rssi_circle_list:
                circ.animate()


    pygame.quit()
