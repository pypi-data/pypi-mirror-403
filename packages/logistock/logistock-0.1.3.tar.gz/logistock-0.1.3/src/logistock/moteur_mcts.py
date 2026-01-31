import math
import random
import copy
import time

class Noeud:
    def __init__(self, etat_pile, sacs_restants, parent=None, action=None):
        self.etat_pile = etat_pile  # Liste des sacs (ex: ["Sable", "Ciment"])
        self.sacs_restants = sacs_restants  # Sacs qu'il reste à poser
        self.parent = parent
        self.action = action
        self.enfants = []
        self.n = 0
        self.somme_couts_evidage = 0 # On utilise ce nom pour le coût d'évidage  # Liste des produits restant à poser
    def est_developpe(self, nb_piles):
        """ Vérifie si toutes les options de piles ont été explorées """
        return len(self.enfants) == nb_piles

    def calculer_ucb(self, N_parent):
        """
                Formule UCB pour la MINIMISATION.
                UCB = Moyenne_Couts - 2 * sqrt(ln(N_parent) / ni)
                """
        if self.n == 0:
            return float('inf') # Priorité à l'exploration
        # MINIMISATION : on veut le coût le plus bas
        moyenne = self.somme_couts_evidage / self.n
        exploration = 2 * math.sqrt(math.log(N_parent) / self.n)
        return moyenne - exploration




class MCTS_Optimiseur:
    def __init__(self, config):
        self.config = config
        self.racine = None  # Permet de conserver l'arbre en mémoire


    def rechercher_meilleur_rangement(self, tous_les_sacs, n_simulations=1000):
        """
        L'algorithme cherche la meilleure séquence d'empilage.
        """
        # Initialisation de la racine : pile vide, tous les sacs à poser
        self.racine = Noeud([], tous_les_sacs)

        for _ in range(n_simulations):
            # 1. Sélection & Développement
            noeud = self._selection_et_developpement(self.racine)

            # 2. Simulation (Rollout) : Calcul de l'espérance de coût d'évidage total
            cout_estime = self._simulation_evidage_total(noeud.etat_pile, noeud.sacs_restants)

            # 3. Rétropropagation
            self._retropropagation(noeud, cout_estime)

        # Extraction du meilleur chemin trouvé
        return self._extraire_meilleure_pile()

    def _selection_et_developpement(self, noeud):
        """ Descend dans l'arbre ou crée un nouveau nœud si possible """
        while noeud.sacs_restants:
            types_possibles = list(set(noeud.sacs_restants))
            if len(noeud.enfants) < len(types_possibles):
                # On développe un nouveau type de produit à cet étage
                deja_testes = [e.action for e in noeud.enfants]
                choix = random.choice([t for t in types_possibles if t not in deja_testes])

                nouvelle_pile = noeud.etat_pile + [choix]
                nouveaux_restants = list(noeud.sacs_restants)
                nouveaux_restants.remove(choix)

                nouvel_enfant = Noeud(nouvelle_pile, nouveaux_restants, parent=noeud, action=choix)
                noeud.enfants.append(nouvel_enfant)
                return nouvel_enfant
            else:
                # On descend via UCB (on cherche le minimum)
                noeud = min(noeud.enfants, key=lambda c: c.calculer_ucb(noeud.n))
        return noeud



    def _simulation_evidage_total(self, pile_partielle, sacs_restants):
        """ Calcule l'espérance de coût totale (E = P * C) """
        """
                Simule le vidage d'une pile complétée aléatoirement.
                Calcul : Somme sur chaque étape du vidage de (Pij * Cij)
                """
        # On complète la pile aléatoirement pour tester un rangement complet
        pile_complete = pile_partielle + random.sample(sacs_restants, len(sacs_restants))
        temp_pile = list(pile_complete)
        esperance_totale = 0

        while len(temp_pile) > 0:
            somme_lambda = sum(self.config.intensites.get(s, 0.1) for s in temp_pile)
            esperance_etape = 0

            for i, sac_id in enumerate(temp_pile):
                k = len(temp_pile) - 1 - i  # Nb de sacs au-dessus
                pi = self.config.intensites.get(sac_id, 0.1) / somme_lambda
                ci = 1 + 2 * k
                esperance_etape += pi * ci

            esperance_totale += esperance_etape
            # On simule le retrait d'un sac au hasard pour l'étape suivante
            temp_pile.pop(random.randint(0, len(temp_pile) - 1))

        return esperance_totale
    def _retropropagation(self, noeud, cout):
        while noeud:
            noeud.n += 1
            noeud.somme_couts_evidage += cout
            noeud = noeud.parent

    def _extraire_meilleure_pile(self):
        chemin = []
        courant = self.racine
        while courant.enfants:
            courant = max(courant.enfants, key=lambda c: c.n)
            chemin.append(courant.action)

        score_final = courant.somme_couts_evidage / courant.n if courant.n > 0 else 0
        return chemin[::-1], score_final  # Renvoie Sommet -> Bas
    def sauvegarder_arbre_dans_json(self):
                """
                Convertit l'arbre MCTS actuel en dictionnaire et l'enregistre via la config.
                """
                if self.racine is None:
                    return

                def noeud_vers_dict(noeud):
                    return {
                        "etat": noeud.etat_pile,
                        "n": noeud.n,
                        "somme_couts": noeud.somme_couts_evidage,
                        "sacs_restants": noeud.sacs_restants,
                        "action": noeud.action,
                        "enfants": [noeud_vers_dict(e) for e in noeud.enfants]
                    }

                arbre_dict = noeud_vers_dict(self.racine)
                # On utilise la classe Configuration pour sauvegarder sur le disque
                self.config.sauvegarder_donnees_specifiques("arbre_mcts", arbre_dict)
                print("💾 Intelligence de l'arbre MCTS sauvegardée.")

    def charger_arbre_depuis_json(self):
                """
                Reconstruit l'arbre MCTS à partir des données stockées dans le JSON.
                """
                donnees = self.config.charger_donnees_specifiques("arbre_mcts")
                if not donnees:
                    print("ℹ️ Aucun arbre précédent trouvé. Création d'un nouvel arbre.")
                    return

                def dict_vers_noeud(d, parent=None):
                    n = Noeud(d["etat"], d["sacs_restants"], parent=parent, action=d["action"])
                    n.n = d["n"]
                    n.somme_couts_evidage = d["somme_couts"]
                    n.enfants = [dict_vers_noeud(e, parent=n) for e in d["enfants"]]
                    return n

                self.racine = dict_vers_noeud(donnees)
                print("🧠 Intelligence MCTS restaurée. Reprise de l'optimisation...")