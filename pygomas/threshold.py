class Threshold(object):

    def __init__(self):
        self.health = 50
        self.ammo = 50
        self.aim = 1
        self.shot = 1
        self.look = 1

    '''/**
    * Get the stablished limit of health. Agent can perform some actions if
    * its health is lower than this value.
    *
    * @return m_iHealth: current threshold for health
    *
    */'''
    def get_health(self):
        return self.health

    '''/**
    * Get the stablished limit of ammunition. Agent can perform some actions
    * if its ammo is lower than this value.
    *
    * @return m_iAmmo: current threshold for ammo
    *
    */'''
    def get_ammo(self):
        return self.ammo

    '''/**
    * Get the stablished number of times that the agent must aim the enemy
    * before to shoot.
    *
    * @return m_iAim: current threshold for aim
    *
    */'''
    def get_aim(self):
        return self.aim

    '''/**
    * Get the stablished number of times that the agent must shoot
    * consecutively before doing other action.
    *
    * @return m_iShot: current threshold for shot
    *
    */'''
    def get_shot(self):
        return self.shot

    '''/**
    * Get the stablished number of times (cycles) that the agent must wait
    * (moving blindly) before looking again.
    *
    * @return m_iLook: current threshold for look
    *
    */'''
    def get_look(self):
        return self.look

    '''/**
    * Stablish the limit of health. Agent can perform some actions if its
    * health is lower than this value.
    * Rank is [0..100].
    *
    * @param _iHealth desired threshold for health
    *
    */'''
    def set_health(self, health):
        if health > 100:
            health = 100
        if health < 0:
            health = 0
        self.health = health

    '''/**
    * Stablish the limit of ammunition. Agent can perform some actions if its
    * ammo is lower than this value.
    * Rank is [0..100].
    *
    * @param _iAmmo desired threshold for ammo
    *
    */'''
    def set_ammo(self, ammo):
        if ammo > 100:
            ammo = 100
        if ammo < 0:
            ammo = 0
        self.ammo = ammo

    '''/**
    * Stablish the number of times that the agent must aim the enemy before
    * to shoot.
    * Rank is [1..20].
    *
    * @param _iAim desired threshold for aim
    *
    */'''
    def set_aim(self, aim):
        if aim > 20:
            aim = 20
        if aim < 1:
            aim = 1
        self.aim = aim

    '''/**
    * Stablish the number of times that the agent must shoot consecutively
    * before doing other action.
    * Rank is [1..20].
    *
    * @param _iShot desired threshold for shot
    *
    */'''
    def set_shot(self, shot):
        if shot > 20:
            shot = 20
        if shot < 1:
            shot = 1
        self.shot = shot

    '''/**
    * Stablish the number of times (cycles) that the agent must wait (moving
    * blindly) before looking again.
    * Rank is [0..100].
    * @param _iLook desired threshold for look
    *
    */'''
    def set_look(self, look):
        if look > 100:
            look = 100
        if look < 0:
            look = 0
        self.look = look
