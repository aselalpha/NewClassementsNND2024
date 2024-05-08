class Poincon:

    def __init__(self, epreuve, signaleur: str, badgeuse: int, role: str, bonus_points: float):
        self.epreuve = epreuve
        self.signaleur = signaleur
        self.badgeuse = badgeuse
        self.role = role
        self.bonus_points = bonus_points

        self.is_debut_mg = False
        self.is_fin_mg = False
    
    def __eq__(self, other):
        """Compare deux objets Poincon, qui sont considérés comme identiques si ils ont même signaleur. 1 signaleur = 1 poinçonnage."""

        if isinstance(self, other.__class__):
            return self.signaleur == other.signaleur
        return False
    
    def __repr__(self):
        if self.is_debut_mg:
            debut_mg = 'Debut MG'
        else:
            debut_mg = ''
        if self.is_fin_mg:
            fin_mg = 'Fin MG'
        else:
            fin_mg = ''
        return f"Poinçon({self.signaleur}, {self.badgeuse}, {self.role}, {debut_mg}, {fin_mg})"