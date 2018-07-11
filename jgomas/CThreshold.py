class CThreshold:

    def __init__(self):
        self.m_iHealth = 50
        self.m_iAmmo = 50
        self.m_iAim = 1
        self.m_iShot = 1
        self.m_iLook = 1

    '''/**
    * Get the stablished limit of health. Agent can perform some actions if
    * its health is lower than this value.
    *
    * @return m_iHealth: current threshold for health
    *
    */'''
    def GetHealth(self):
        return self.m_iHealth

    '''/**
    * Get the stablished limit of ammunition. Agent can perform some actions
    * if its ammo is lower than this value.
    *
    * @return m_iAmmo: current threshold for ammo
    *
    */'''
    def GetAmmo(self):
        return self.m_iAmmo

    '''/**
    * Get the stablished number of times that the agent must aim the enemy
    * before to shoot.
    *
    * @return m_iAim: current threshold for aim
    *
    */'''
    def GetAim(self):
        return self.m_iAim

    '''/**
    * Get the stablished number of times that the agent must shoot
    * consecutively before doing other action.
    *
    * @return m_iShot: current threshold for shot
    *
    */'''
    def GetShot(self):
        return self.m_iShot

    '''/**
    * Get the stablished number of times (cycles) that the agent must wait
    * (moving blindly) before looking again.
    *
    * @return m_iLook: current threshold for look
    *
    */'''
    def GetLook(self):
        return self.m_iLook

    '''/**
    * Stablish the limit of health. Agent can perform some actions if its
    * health is lower than this value.
    * Rank is [0..100].
    *
    * @param _iHealth desired threshold for health
    *
    */'''
    def SetHealth(self, _iHealth):
        if _iHealth > 100:
            _iHealth = 100
        if _iHealth < 0:
            _iHealth = 0
        self.m_iHealth = _iHealth

    '''/**
    * Stablish the limit of ammunition. Agent can perform some actions if its
    * ammo is lower than this value.
    * Rank is [0..100].
    *
    * @param _iAmmo desired threshold for ammo
    *
    */'''
    def SetAmmo(self, _iAmmo):
        if _iAmmo > 100:
            _iAmmo = 100
        if _iAmmo < 0:
            _iAmmo = 0
        self.m_iAmmo = _iAmmo

    '''/**
    * Stablish the number of times that the agent must aim the enemy before
    * to shoot.
    * Rank is [1..20].
    *
    * @param _iAim desired threshold for aim
    *
    */'''
    def SetAim(self, _iAim):
        if _iAim > 20:
            _iAim = 20
        if _iAim < 1:
            _iAim = 1
        self.m_iAim = _iAim

    '''/**
    * Stablish the number of times that the agent must shoot consecutively
    * before doing other action.
    * Rank is [1..20].
    *
    * @param _iShot desired threshold for shot
    *
    */'''
    def SetShot(self, _iShot):
        if _iShot > 20:
            _iShot = 20
        if _iShot < 1:
            _iShot = 1
        self.m_iShot = _iShot

    '''/**
    * Stablish the number of times (cycles) that the agent must wait (moving
    * blindly) before looking again.
    * Rank is [0..100].
    * @param _iLook desired threshold for look
    *
    */'''
    def SetLook(self, _iLook):
        if _iLook > 100:
            _iLook = 100
        if _iLook < 0:
            _iLook = 0
        self.m_iLook = _iLook
