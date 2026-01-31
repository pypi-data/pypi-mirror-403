/**
 * Lucy Assist - Composant Alpine.js pour le chatbot
 *
 * Ce fichier contient toute la logique client du chatbot Lucy Assist.
 * Il utilise Alpine.js pour la réactivité et communique avec le backend Django via des API REST.
 */

function lucyAssist() {
    return {
        // État de l'interface
        isOpen: false,
        isLoading: false,
        showHistory: false,
        showDoc: false,
        showBuyCredits: false,
        showFeedback: false,
        showGuide: false,
        guideStep: 1,
        hasNewMessage: false,
        hasError: false,
        lucyDidNotUnderstand: false,

        // Données
        currentMessage: '',
        messages: [],
        conversations: [],
        suggestions: [],
        currentConversationId: null,
        tokensDisponibles: 0,
        buyAmount: 10,
        feedbackDescription: '',
        feedbackSending: false,

        // Configuration
        apiBaseUrl: '/lucy-assist/api',
        csrfToken: '',

        /**
         * Initialisation du composant
         */
        init() {
            // Récupérer le token CSRF
            this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                            this.getCookie('csrftoken');

            // Restaurer l'état depuis sessionStorage
            this.restoreState();

            // Charger les données initiales
            this.loadTokenStatus();
            this.loadConversations().then(() => {
                // Recharger la conversation en cours si elle existe
                if (this.currentConversationId) {
                    this.loadConversation(this.currentConversationId);
                }
            });
            this.loadSuggestions();

            // Vérifier si c'est le premier lancement
            this.checkFirstLaunch();

            // Sauvegarder l'état quand isOpen change
            this.$watch('isOpen', (value) => {
                this.saveState();
                if (value) {
                    this.$nextTick(() => {
                        this.$refs.messageInput?.focus();
                    });
                }
            });

            // Sauvegarder l'état quand la conversation change
            this.$watch('currentConversationId', () => {
                this.saveState();
            });

            // Sauvegarder avant de quitter la page
            window.addEventListener('beforeunload', () => {
                this.saveState();
            });
        },

        /**
         * Sauvegarde l'état dans sessionStorage
         */
        saveState() {
            const state = {
                isOpen: this.isOpen,
                currentConversationId: this.currentConversationId,
                showHistory: this.showHistory,
                showDoc: this.showDoc
            };
            sessionStorage.setItem('lucy_assist_state', JSON.stringify(state));
        },

        /**
         * Restaure l'état depuis sessionStorage
         */
        restoreState() {
            try {
                const savedState = sessionStorage.getItem('lucy_assist_state');
                if (savedState) {
                    const state = JSON.parse(savedState);
                    this.isOpen = state.isOpen || false;
                    this.currentConversationId = state.currentConversationId || null;
                    this.showHistory = state.showHistory || false;
                    this.showDoc = state.showDoc || false;
                }
            } catch (e) {
                console.error('Erreur restauration état Lucy Assist:', e);
            }
        },

        /**
         * Gestion des raccourcis clavier
         */
        handleKeydown(event) {
            // Ctrl+K pour ouvrir
            if (event.ctrlKey && event.key === 'k') {
                event.preventDefault();
                this.toggleSidebar();
            }

            // Echap pour fermer
            if (event.key === 'Escape' && this.isOpen) {
                this.closeSidebar();
            }
        },

        /**
         * Toggle du sidebar
         */
        toggleSidebar() {
            this.isOpen = !this.isOpen;
            if (this.isOpen) {
                this.hasNewMessage = false;
            }
            this.saveState();
        },

        /**
         * Fermeture du sidebar
         */
        closeSidebar() {
            this.isOpen = false;
            this.saveState();
            this.showHistory = false;
            this.showDoc = false;
        },

        /**
         * Vérifie si c'est le premier lancement
         */
        checkFirstLaunch() {
            const hasSeenGuide = localStorage.getItem('lucy_assist_guide_seen');
            if (!hasSeenGuide && this.conversations.length === 0) {
                // Afficher le guide au premier chargement si pas de conversations
                setTimeout(() => {
                    if (this.conversations.length === 0) {
                        this.showGuide = true;
                        this.isOpen = true;
                    }
                }, 2000);
            }
        },

        /**
         * Navigation dans le guide
         */
        nextGuideStep() {
            this.guideStep++;
        },

        skipGuide() {
            this.finishGuide();
        },

        finishGuide() {
            this.showGuide = false;
            localStorage.setItem('lucy_assist_guide_seen', 'true');
        },

        /**
         * Charge le statut des tokens
         */
        async loadTokenStatus() {
            try {
                const response = await this.apiGet('/tokens/status');
                this.tokensDisponibles = response.tokens_disponibles || 0;
            } catch (error) {
                console.error('Erreur chargement tokens:', error);
            }
        },

        /**
         * Charge la liste des conversations
         */
        async loadConversations() {
            try {
                const response = await this.apiGet('/conversations');
                this.conversations = response.conversations || [];
            } catch (error) {
                console.error('Erreur chargement conversations:', error);
            }
        },

        /**
         * Charge les suggestions
         */
        async loadSuggestions() {
            try {
                const response = await this.apiGet('/suggestions');
                this.suggestions = response.suggestions || [];
            } catch (error) {
                console.error('Erreur chargement suggestions:', error);
                // Suggestions par défaut
                this.suggestions = [
                    "Comment créer un nouveau membre ?",
                    "Comment effectuer un paiement ?",
                    "Où trouver la liste des adhésions ?"
                ];
            }
        },

        /**
         * Crée une nouvelle conversation
         */
        async newConversation() {
            try {
                const response = await this.apiPost('/conversations', {
                    page_contexte: window.location.pathname
                });

                this.currentConversationId = response.id;
                this.messages = [];
                this.showHistory = false;
                this.showDoc = false;
                this.saveState();

                // Recharger les conversations
                await this.loadConversations();

            } catch (error) {
                console.error('Erreur création conversation:', error);
                this.showToast('Erreur lors de la création de la conversation', 'error');
            }
        },

        /**
         * Charge une conversation existante
         */
        async loadConversation(conversationId) {
            try {
                const response = await this.apiGet(`/conversations/${conversationId}`);

                this.currentConversationId = conversationId;
                this.messages = response.messages || [];
                this.showHistory = false;
                this.saveState();

                // Scroll vers le bas avec un petit délai pour laisser le DOM se mettre à jour
                this.$nextTick(() => {
                    setTimeout(() => {
                        this.scrollToBottom();
                    }, 100);
                });

            } catch (error) {
                console.error('Erreur chargement conversation:', error);
                // Si la conversation n'existe plus, réinitialiser
                this.currentConversationId = null;
                this.messages = [];
                this.saveState();
                this.showToast('Erreur lors du chargement de la conversation', 'error');
            }
        },

        /**
         * Supprime une conversation
         */
        async deleteConversation(conversationId) {
            if (!confirm('Êtes-vous sûr de vouloir supprimer cette conversation ?')) {
                return;
            }

            try {
                await this.apiDelete(`/conversations/${conversationId}`);

                // Recharger les conversations
                await this.loadConversations();

                // Si c'était la conversation courante, reset
                if (this.currentConversationId === conversationId) {
                    this.currentConversationId = null;
                    this.messages = [];
                }

                this.showToast('Conversation supprimée', 'success');

            } catch (error) {
                console.error('Erreur suppression conversation:', error);
                this.showToast('Erreur lors de la suppression', 'error');
            }
        },

        /**
         * Envoie le message courant
         */
        async sendCurrentMessage() {
            const message = this.currentMessage.trim();
            if (!message) return;

            await this.sendMessage(message);
        },

        /**
         * Envoie un message (depuis l'input ou une suggestion)
         */
        async sendMessage(message) {
            if (this.isLoading) return;

            // Réinitialiser le flag "Lucy n'a pas compris" pour le nouveau message
            this.lucyDidNotUnderstand = false;

            // Créer une conversation si nécessaire
            if (!this.currentConversationId) {
                await this.newConversation();
            }

            // Ajouter le message utilisateur à l'affichage
            const userMessage = {
                id: Date.now(),
                repondant: 'UTILISATEUR',
                contenu: message,
                created_date: new Date().toISOString(),
                tokens_utilises: 0
            };
            this.messages.push(userMessage);
            this.currentMessage = '';

            // Scroll vers le bas
            this.$nextTick(() => {
                this.scrollToBottom();
            });

            // Envoyer au serveur
            try {
                this.isLoading = true;

                // Envoyer le message utilisateur
                await this.apiPost(`/conversations/${this.currentConversationId}/messages`, {
                    contenu: message
                });

                // Demander une réponse à Claude (avec streaming)
                await this.streamChatCompletion();

            } catch (error) {
                console.error('Erreur envoi message:', error);

                if (error.status === 402) {
                    // Pas assez de crédits
                    this.showBuyCredits = true;
                } else {
                    // Marquer qu'il y a eu une erreur pour proposer le feedback
                    this.hasError = true;
                    this.showToast('Erreur lors de l\'envoi du message', 'error');
                }

            } finally {
                this.isLoading = false;
            }
        },

        /**
         * Stream la réponse de Claude
         */
        async streamChatCompletion() {
            const url = `${this.apiBaseUrl}/conversations/${this.currentConversationId}/chat`;

            // Index du message bot dans le tableau
            const botMessageIndex = this.messages.length;

            // Créer un placeholder pour la réponse
            this.messages.push({
                id: Date.now() + 1,
                repondant: 'CHATBOT',
                contenu: '',
                created_date: new Date().toISOString(),
                tokens_utilises: 0
            });

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    },
                    body: JSON.stringify({
                        page_contexte: window.location.pathname
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw { status: response.status, ...errorData };
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullContent = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const text = decoder.decode(value);
                    const lines = text.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));

                                if (data.type === 'content') {
                                    fullContent += data.content;
                                    // Forcer la réactivité Alpine en réassignant l'objet
                                    this.messages[botMessageIndex] = {
                                        ...this.messages[botMessageIndex],
                                        contenu: fullContent
                                    };
                                    this.$nextTick(() => this.scrollToBottom());
                                } else if (data.type === 'done') {
                                    // Mise à jour finale avec l'ID et les tokens
                                    this.messages[botMessageIndex] = {
                                        ...this.messages[botMessageIndex],
                                        id: data.message_id,
                                        tokens_utilises: data.tokens_utilises
                                    };
                                    // Mettre à jour les tokens
                                    await this.loadTokenStatus();
                                } else if (data.type === 'error') {
                                    throw new Error(data.error);
                                }
                            } catch (e) {
                                if (e.message) throw e;
                            }
                        }
                    }
                }

                // Supprimer le message placeholder s'il est resté vide
                if (!this.messages[botMessageIndex]?.contenu) {
                    this.messages.splice(botMessageIndex, 1);
                }

                // Vérifier si Lucy n'a pas compris le message
                const botResponse = this.messages[botMessageIndex]?.contenu || '';
                this.lucyDidNotUnderstand = this.checkIfLucyDidNotUnderstand(botResponse);

                // Réinitialiser le flag d'erreur après une réponse réussie (sauf si Lucy n'a pas compris)
                if (!this.lucyDidNotUnderstand) {
                    this.hasError = false;
                }

                // Recharger les conversations pour mettre à jour les titres
                await this.loadConversations();

            } catch (error) {
                // Marquer qu'il y a eu une erreur
                this.hasError = true;

                // Supprimer le message placeholder vide en cas d'erreur
                if (botMessageIndex < this.messages.length && !this.messages[botMessageIndex]?.contenu) {
                    this.messages.splice(botMessageIndex, 1);
                }
                throw error;
            }
        },

        /**
         * Vérifie si Lucy n'a pas compris ou ne peut pas aider l'utilisateur
         */
        checkIfLucyDidNotUnderstand(response) {
            if (!response) return false;

            const lowerResponse = response.toLowerCase();

            // Patterns indiquant que Lucy n'a pas compris ou ne peut pas aider
            const notUnderstoodPatterns = [
                // Ne comprend pas
                'je ne comprends pas',
                'je n\'ai pas compris',
                'je n\'arrive pas à comprendre',
                'pourriez-vous reformuler',
                'pouvez-vous reformuler',
                'pourriez-vous préciser',
                'pouvez-vous préciser',
                'je ne suis pas sûr de comprendre',
                'je ne suis pas certain de comprendre',
                'votre message n\'est pas clair',
                'erreur de frappe',
                'erreur de saisie',
                'message incompréhensible',
                'je n\'ai pas pu interpréter',
                'que souhaitez-vous faire',
                'que voulez-vous faire',
                // Ne peut pas aider / pas accès
                'je n\'ai pas accès',
                'je n\'ai pas les outils',
                'je n\'ai pas la possibilité',
                'je ne peux pas',
                'je ne suis pas en mesure',
                'pas accès aux outils',
                'outils nécessaires',
                'fonctionnalité non disponible',
                'cette fonctionnalité n\'est pas',
                'je ne dispose pas',
                'mes outils actuels ne permettent pas',
                'mes outils ne permettent pas',
                'je n\'arrive pas à',
                'impossible de réaliser',
                'je ne trouve pas',
                'modèle non disponible',
                'n\'existe pas dans',
                // Questions de clarification multiples
                'pouvez-vous me dire',
                'pourriez-vous me préciser',
                'solutions possibles',
                // Hors du périmètre / redirection vers autres outils
                'je suis spécialisée',
                'je vous recommande de consulter',
                'je vous conseille de',
                'en dehors de mon périmètre',
                'hors de mon champ',
                'ne fait pas partie de mes compétences',
                'dépasse mes capacités',
                'assistants culinaires',
                'chatgpt',
                'google assistant',
                'sites spécialisés',
                'comment puis-je vous aider avec votre crm',
                'y a-t-il quelque chose que vous souhaitez faire'
            ];

            return notUnderstoodPatterns.some(pattern => lowerResponse.includes(pattern));
        },

        /**
         * Ouvre le modal de feedback
         */
        openFeedback() {
            this.showFeedback = true;
            this.feedbackDescription = '';
        },

        /**
         * Ferme le modal de feedback
         */
        closeFeedback() {
            this.showFeedback = false;
            this.feedbackDescription = '';
        },

        /**
         * Envoie le feedback à Revolucy
         */
        async sendFeedback() {
            if (!this.currentConversationId) {
                this.showToast('Aucune conversation à signaler', 'warning');
                return;
            }

            this.feedbackSending = true;

            try {
                const response = await this.apiPost('/feedback', {
                    conversation_id: this.currentConversationId,
                    description: this.feedbackDescription,
                    page_url: window.location.href
                });

                this.showToast(response.message || 'Feedback envoyé avec succès !', 'success');
                this.closeFeedback();
                this.hasError = false;
                this.lucyDidNotUnderstand = false;

            } catch (error) {
                console.error('Erreur envoi feedback:', error);
                this.showToast('Erreur lors de l\'envoi du feedback', 'error');
            } finally {
                this.feedbackSending = false;
            }
        },

        /**
         * Achat de crédits
         */
        async buyCredits() {
            if (this.buyAmount < 10) {
                this.showToast('Le montant minimum est de 10 EUR', 'warning');
                return;
            }

            try {
                const response = await this.apiPost('/tokens/buy', {
                    montant_ht: this.buyAmount
                });

                // Ouvrir l'URL de souscription dans un nouvel onglet
                window.open(response.url_souscription, '_blank');

                this.showBuyCredits = false;
                this.showToast('Redirection vers la page de paiement...', 'info');

            } catch (error) {
                console.error('Erreur achat crédits:', error);
                this.showToast('Erreur lors de la génération du lien de paiement', 'error');
            }
        },

        /**
         * Calcule le nombre de tokens pour un montant
         */
        calculateTokens(amount) {
            return Math.floor((amount / 10) * 1000000);
        },

        /**
         * Formate un nombre de tokens
         */
        formatTokens(tokens) {
            if (tokens >= 1000000) {
                return (tokens / 1000000).toFixed(1) + 'M';
            } else if (tokens >= 1000) {
                return (tokens / 1000).toFixed(0) + 'K';
            }
            return tokens.toString();
        },

        /**
         * Calcule et formate le coût en euros pour un nombre de tokens
         * Prix par défaut: 10€ par million de tokens
         */
        formatTokenCost(tokens) {
            const prixParMillion = 10; // 10€ par million de tokens
            const cout = (tokens / 1000000) * prixParMillion;
            return cout.toFixed(4) + '€';
        },

        /**
         * Formate une date
         */
        formatDate(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diff = now - date;

            // Moins d'une minute
            if (diff < 60000) {
                return 'À l\'instant';
            }

            // Moins d'une heure
            if (diff < 3600000) {
                const minutes = Math.floor(diff / 60000);
                return `Il y a ${minutes} min`;
            }

            // Aujourd'hui
            if (date.toDateString() === now.toDateString()) {
                return `Aujourd'hui à ${date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`;
            }

            // Cette semaine
            if (diff < 7 * 24 * 3600000) {
                return date.toLocaleDateString('fr-FR', { weekday: 'long', hour: '2-digit', minute: '2-digit' });
            }

            return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
        },

        /**
         * Formate une heure
         */
        formatTime(dateString) {
            const date = new Date(dateString);
            return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
        },

        /**
         * Formate le contenu d'un message (markdown basique)
         */
        formatMessage(content) {
            if (!content) return '';

            // Échapper le HTML
            let formatted = content
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');

            // Markdown basique
            formatted = formatted
                // Gras
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                // Italique
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                // Code inline
                .replace(/`(.*?)`/g, '<code class="bg-base-300 px-1 rounded">$1</code>')
                // Liens
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="link link-primary">$1</a>')
                // Sauts de ligne
                .replace(/\n/g, '<br>');

            return formatted;
        },

        /**
         * Scroll vers le bas de la zone de messages
         */
        scrollToBottom() {
            const container = this.$refs.messagesContainer;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        },

        /**
         * Affiche un toast de notification
         */
        showToast(message, type = 'info') {
            // Utiliser le système de toast Alpine.js existant si disponible
            if (window.Alpine && window.toastData) {
                window.toastData.show(message, type);
            } else {
                // Fallback: alert simple
                console.log(`[${type}] ${message}`);
            }
        },

        /**
         * Récupère un cookie
         */
        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        // Méthodes utilitaires pour les appels API
        async apiGet(endpoint) {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw { status: response.status, ...error };
            }

            return response.json();
        },

        async apiPost(endpoint, data) {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw { status: response.status, ...error };
            }

            return response.json();
        },

        async apiDelete(endpoint) {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw { status: response.status, ...error };
            }

            return response.json();
        }
    };
}

// Exposer la fonction globalement pour que x-data puisse y accéder
window.lucyAssist = lucyAssist;

// Enregistrer le composant avec Alpine si disponible
document.addEventListener('DOMContentLoaded', () => {
    if (window.Alpine && window.Alpine.data) {
        window.Alpine.data('lucyAssist', lucyAssist);
    }
});
