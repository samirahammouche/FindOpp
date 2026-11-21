from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import Categorie, Evenement, StatutEvenement


def jeton(user_id, role):
    # Fabrique un faux jeton comme celui du service Auth
    token = AccessToken()
    token['user_id'] = user_id
    token['role'] = role
    return f'Bearer {token}'


class BaseTest(APITestCase):
    def setUp(self):
        self.cat = Categorie.objects.create(nom='Bourse')
        self.cat2 = Categorie.objects.create(nom='Stage')
        self.demain = timezone.localdate() + timedelta(days=1)
        self.hier = timezone.localdate() - timedelta(days=1)

    def creer(self, titre='Salon', statut=StatutEvenement.APPROUVEE,
              organisateur=1, date=None, categorie=None):
        return Evenement.objects.create(
            titre=titre, description='desc', dateLimite=date or self.demain,
            statut=statut, organisateurId=organisateur,
            categorie=categorie or self.cat)

    def connecter(self, user_id, role):
        self.client.credentials(HTTP_AUTHORIZATION=jeton(user_id, role))


class PublicTests(BaseTest):
    def test_public_ne_voit_que_les_approuves_non_expires(self):
        self.creer('visible')
        self.creer('brouillon', statut=StatutEvenement.BROUILLON)
        self.creer('attente', statut=StatutEvenement.EN_ATTENTE)
        self.creer('rejete', statut=StatutEvenement.REJETEE)
        self.creer('expire', date=self.hier)
        r = self.client.get('/api/events/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([e['titre'] for e in r.data['results']], ['visible'])

    def test_detail_non_approuve_donne_404(self):
        e = self.creer(statut=StatutEvenement.BROUILLON)
        r = self.client.get(f'/api/events/{e.id}/')
        self.assertEqual(r.status_code, 404)

    def test_recherche_par_mot_cle(self):
        self.creer('Salon du livre')
        self.creer('Concours de robotique')
        r = self.client.get('/api/events/?search=livre')
        self.assertEqual([e['titre'] for e in r.data['results']], ['Salon du livre'])

    def test_filtre_par_categorie(self):
        self.creer('A', categorie=self.cat)
        self.creer('B', categorie=self.cat2)
        r = self.client.get(f'/api/events/?categorie={self.cat2.id}')
        self.assertEqual([e['titre'] for e in r.data['results']], ['B'])

    def test_creation_de_categorie_reservee_a_ladmin(self):
        r = self.client.post('/api/events/categories/', {'nom': 'X'})
        self.assertEqual(r.status_code, 401)
        self.connecter(1, 'ORGANIZER')
        r = self.client.post('/api/events/categories/', {'nom': 'X'})
        self.assertEqual(r.status_code, 403)
        self.connecter(99, 'ADMIN')
        r = self.client.post('/api/events/categories/', {'nom': 'X'})
        self.assertEqual(r.status_code, 201)


class OrganisateurTests(BaseTest):
    def corps(self, **extra):
        data = {'titre': 'Nouveau', 'description': 'texte',
                'dateLimite': str(self.demain), 'categorie': self.cat.id}
        data.update(extra)
        return data

    def test_creation_exige_un_token(self):
        r = self.client.post('/api/events/mine/', self.corps())
        self.assertEqual(r.status_code, 401)

    def test_admin_ne_peut_pas_creer(self):
        self.connecter(99, 'ADMIN')
        r = self.client.post('/api/events/mine/', self.corps())
        self.assertEqual(r.status_code, 403)

    def test_creation_force_brouillon_et_organisateur(self):
        self.connecter(7, 'ORGANIZER')
        r = self.client.post('/api/events/mine/',
                             self.corps(statut='APPROUVEE', organisateurId=999),
                             format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['statut'], 'BROUILLON')
        self.assertEqual(r.data['organisateurId'], 7)

    def test_date_limite_passee_refusee(self):
        self.connecter(1, 'ORGANIZER')
        r = self.client.post('/api/events/mine/',
                             self.corps(dateLimite=str(self.hier)))
        self.assertEqual(r.status_code, 400)

    def test_mes_evenements_ne_montre_que_les_miens(self):
        self.creer('a moi', organisateur=1, statut=StatutEvenement.BROUILLON)
        self.creer('a lui', organisateur=2, statut=StatutEvenement.BROUILLON)
        self.connecter(1, 'ORGANIZER')
        r = self.client.get('/api/events/mine/')
        self.assertEqual([e['titre'] for e in r.data['results']], ['a moi'])

    def test_modifier_son_brouillon(self):
        e = self.creer(statut=StatutEvenement.BROUILLON, organisateur=1)
        self.connecter(1, 'ORGANIZER')
        r = self.client.patch(f'/api/events/mine/{e.id}/', {'titre': 'Autre titre'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['titre'], 'Autre titre')

    def test_modifier_evenement_dun_autre_donne_403(self):
        e = self.creer(statut=StatutEvenement.BROUILLON, organisateur=2)
        self.connecter(1, 'ORGANIZER')
        r = self.client.patch(f'/api/events/mine/{e.id}/', {'titre': 'x'})
        self.assertEqual(r.status_code, 403)

    def test_modifier_evenement_approuve_donne_409(self):
        e = self.creer(statut=StatutEvenement.APPROUVEE, organisateur=1)
        self.connecter(1, 'ORGANIZER')
        r = self.client.patch(f'/api/events/mine/{e.id}/', {'titre': 'x'})
        self.assertEqual(r.status_code, 409)

    def test_soumettre_puis_soumettre_encore(self):
        e = self.creer(statut=StatutEvenement.BROUILLON, organisateur=1)
        self.connecter(1, 'ORGANIZER')
        r = self.client.post(f'/api/events/mine/{e.id}/submit/')
        self.assertEqual(r.status_code, 200)
        e.refresh_from_db()
        self.assertEqual(e.statut, StatutEvenement.EN_ATTENTE)
        r = self.client.post(f'/api/events/mine/{e.id}/submit/')
        self.assertEqual(r.status_code, 409)

    def test_supprimer_evenement_dun_autre_donne_403(self):
        e = self.creer(organisateur=2)
        self.connecter(1, 'ORGANIZER')
        r = self.client.delete(f'/api/events/mine/{e.id}/')
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Evenement.objects.filter(id=e.id).exists())


class AdminTests(BaseTest):
    def test_organisateur_ne_peut_pas_approuver(self):
        e = self.creer(statut=StatutEvenement.EN_ATTENTE)
        self.connecter(1, 'ORGANIZER')
        r = self.client.post(f'/api/events/moderation/{e.id}/approve/')
        self.assertEqual(r.status_code, 403)

    def test_approuver(self):
        e = self.creer(statut=StatutEvenement.EN_ATTENTE)
        self.connecter(99, 'ADMIN')
        r = self.client.post(f'/api/events/moderation/{e.id}/approve/')
        self.assertEqual(r.status_code, 200)
        e.refresh_from_db()
        self.assertEqual(e.statut, StatutEvenement.APPROUVEE)

    def test_rejeter_puis_resoumettre(self):
        e = self.creer(statut=StatutEvenement.EN_ATTENTE, organisateur=1)
        self.connecter(99, 'ADMIN')
        r = self.client.post(f'/api/events/moderation/{e.id}/reject/')
        self.assertEqual(r.status_code, 200)
        self.connecter(1, 'ORGANIZER')
        r = self.client.post(f'/api/events/mine/{e.id}/submit/')
        self.assertEqual(r.status_code, 200)

    def test_approuver_un_brouillon_donne_409(self):
        e = self.creer(statut=StatutEvenement.BROUILLON)
        self.connecter(99, 'ADMIN')
        r = self.client.post(f'/api/events/moderation/{e.id}/approve/')
        self.assertEqual(r.status_code, 409)

    def test_file_de_moderation_par_defaut(self):
        self.creer('attente', statut=StatutEvenement.EN_ATTENTE)
        self.creer('brouillon', statut=StatutEvenement.BROUILLON)
        self.connecter(99, 'ADMIN')
        r = self.client.get('/api/events/moderation/')
        self.assertEqual([e['titre'] for e in r.data['results']], ['attente'])

    def test_evenement_approuve_devient_public(self):
        e = self.creer(statut=StatutEvenement.EN_ATTENTE)
        self.connecter(99, 'ADMIN')
        self.client.post(f'/api/events/moderation/{e.id}/approve/')
        self.client.credentials()  # redevenir visiteur
        r = self.client.get('/api/events/')
        self.assertEqual(r.data['count'], 1)
