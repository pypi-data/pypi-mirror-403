"""
Service d'intégration avec Claude API (Anthropic).

Optimisations tokens:
- Cache du contexte projet via ProjectContextService
- Résumé des conversations longues
- Compression intelligente du contexte

Tools CRUD:
- Claude peut exécuter des actions CRUD via les tools
- Les tools sont exécutés côté serveur avec les permissions de l'utilisateur
"""
import json
from typing import Generator, List, Dict, Any

import anthropic

from lucy_assist.utils.log_utils import LogUtils
from lucy_assist.constantes import LucyAssistConstantes
from lucy_assist.services.tools_definition import LUCY_ASSIST_TOOLS
from lucy_assist.conf import lucy_assist_settings


class ClaudeService:
    """Service pour interagir avec l'API Claude d'Anthropic."""

    MAX_TOKENS = 4096

    # Seuils pour l'optimisation
    MAX_MESSAGES_BEFORE_SUMMARY = 10  # Résumer après 10 messages
    MAX_CONTEXT_TOKENS = 2000  # Limiter le contexte à 2000 tokens estimés

    def __init__(self):
        self.api_key = lucy_assist_settings.CLAUDE_LUCY_ASSIST_API_KEY
        if not self.api_key:
            raise ValueError("CLAUDE_LUCY_ASSIST_API_KEY non configurée dans les settings")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self._project_context_service = None
        self._tools = LUCY_ASSIST_TOOLS
        self._model = lucy_assist_settings.CLAUDE_MODEL

    @property
    def project_context_service(self):
        """Lazy loading du service de contexte projet."""
        if self._project_context_service is None:
            from lucy_assist.services.project_context_service import ProjectContextService
            self._project_context_service = ProjectContextService()
        return self._project_context_service

    def _build_system_prompt(
        self,
        page_context: Dict,
        user,
        user_question: str = ""
    ) -> str:
        """
        Construit le prompt système avec le contexte optimisé.

        Utilise le cache pour réduire la redondance des informations
        sur le projet.
        """
        # Récupérer les permissions utilisateur (compressées)
        user_permissions = []
        if hasattr(user, 'get_all_permissions'):
            # Ne garder que les permissions pertinentes (sans préfixe d'app commun)
            all_perms = list(user.get_all_permissions())
            user_permissions = [p.split('.')[-1] for p in all_perms[:15]]

        # Récupérer le contexte projet optimisé depuis le cache
        page_url = page_context.get('page_url', page_context.get('url', ''))
        optimized_context = self.project_context_service.get_optimized_context(
            page_url=page_url,
            user_question=user_question
        )

        # Fusionner le contexte de page avec le contexte projet caché
        enriched_context = {
            'page': page_context,
            'projet': optimized_context.get('relevant_info', {}),
            'cache_stats': optimized_context.get('stats', {})
        }

        # Construire le prompt avec contexte compact
        prompt = LucyAssistConstantes.SYSTEM_PROMPTS['default'].format(
            page_context=json.dumps(enriched_context, ensure_ascii=False, indent=2),
            user_permissions=', '.join(user_permissions)
        )

        # Ajouter les instructions complémentaires si configurées
        from lucy_assist.models import ConfigurationLucyAssist
        config = ConfigurationLucyAssist.get_config()
        if config.prompt_complementaire:
            prompt += f"\n\n## Instructions complémentaires\n{config.prompt_complementaire}"

        return prompt

    def _optimize_messages(self, messages: List) -> List[Dict]:
        """
        Optimise l'historique des messages pour réduire les tokens.

        Pour les conversations longues, résume les anciens messages
        au lieu de les envoyer en entier.
        """
        formatted = self._format_messages(messages)

        if len(formatted) <= self.MAX_MESSAGES_BEFORE_SUMMARY:
            return formatted

        # Résumer la conversation
        summary_data = self.project_context_service.summarize_conversation(
            formatted,
            max_tokens=500
        )

        if not summary_data:
            return formatted

        # Reconstruire les messages avec le résumé
        optimized = []

        # Ajouter les premiers messages
        optimized.extend(summary_data['first_messages'])

        # Ajouter le résumé comme message système
        optimized.append({
            'role': 'user',
            'content': f"[Note: {summary_data['original_count'] - 4} messages résumés]\n{summary_data['summary']}"
        })

        # Ajouter les derniers messages
        optimized.extend(summary_data['last_messages'])

        LogUtils.info(
            f"Conversation optimisée: {len(formatted)} -> {len(optimized)} messages, "
            f"~{summary_data.get('tokens_saved_estimate', 0)} tokens économisés"
        )

        return optimized

    def _format_messages(self, messages: List) -> List[Dict]:
        """Formate les messages pour l'API Claude."""
        formatted = []

        for msg in messages:
            role = "user" if msg.repondant == LucyAssistConstantes.Repondant.UTILISATEUR else "assistant"
            formatted.append({
                "role": role,
                "content": msg.contenu
            })

        return formatted

    def chat_completion_stream(
        self,
        messages: List,
        page_context: Dict,
        user,
        tool_executor=None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Génère une réponse en streaming avec support des tools.

        Args:
            messages: Liste des messages de la conversation
            page_context: Contexte de la page courante
            user: Utilisateur Django
            tool_executor: Callable pour exécuter les tools (optionnel)

        Yields:
            Dict avec 'type' (content/tool_use/tool_result/usage/error) et les données associées
        """
        try:
            # Extraire la question utilisateur du dernier message
            user_question = ""
            if messages:
                last_msg = messages[-1] if hasattr(messages[-1], 'contenu') else messages[-1]
                user_question = getattr(last_msg, 'contenu', '') if hasattr(last_msg, 'contenu') else str(last_msg)

            system_prompt = self._build_system_prompt(page_context, user, user_question)

            # Utiliser l'optimisation des messages pour les longues conversations
            formatted_messages = self._optimize_messages(messages)

            if not formatted_messages:
                yield {'type': 'error', 'error': 'Aucun message à traiter'}
                return

            # Boucle pour gérer les appels de tools
            current_messages = formatted_messages.copy()
            max_tool_iterations = 5  # Limite de sécurité

            for iteration in range(max_tool_iterations):
                with self.client.messages.stream(
                    model=self._model,
                    max_tokens=self.MAX_TOKENS,
                    system=system_prompt,
                    messages=current_messages,
                    tools=self._tools
                ) as stream:
                    response_text = ""
                    tool_uses = []

                    for text in stream.text_stream:
                        response_text += text
                        yield {'type': 'content', 'content': text}

                    # Récupérer la réponse finale pour les tools
                    response = stream.get_final_message()

                    # Extraire les appels de tools
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_uses.append({
                                'id': block.id,
                                'name': block.name,
                                'input': block.input
                            })

                    # Si pas de tool_use, on a fini
                    if not tool_uses or response.stop_reason != "tool_use":
                        if response.usage:
                            total_tokens = response.usage.input_tokens + response.usage.output_tokens
                            yield {
                                'type': 'usage',
                                'input_tokens': response.usage.input_tokens,
                                'output_tokens': response.usage.output_tokens,
                                'total_tokens': total_tokens
                            }
                        return

                    # Exécuter les tools
                    tool_results = []
                    for tool_use in tool_uses:
                        yield {
                            'type': 'tool_use',
                            'tool_name': tool_use['name'],
                            'tool_input': tool_use['input']
                        }

                        # Exécuter le tool si un executor est fourni
                        if tool_executor:
                            try:
                                result = tool_executor(
                                    tool_use['name'],
                                    tool_use['input'],
                                    user
                                )
                                tool_results.append({
                                    'type': 'tool_result',
                                    'tool_use_id': tool_use['id'],
                                    'content': json.dumps(result, ensure_ascii=False)
                                })
                                yield {
                                    'type': 'tool_result',
                                    'tool_name': tool_use['name'],
                                    'result': result
                                }
                            except Exception as e:
                                error_result = {'error': str(e)}
                                tool_results.append({
                                    'type': 'tool_result',
                                    'tool_use_id': tool_use['id'],
                                    'content': json.dumps(error_result),
                                    'is_error': True
                                })
                                yield {
                                    'type': 'tool_error',
                                    'tool_name': tool_use['name'],
                                    'error': str(e)
                                }
                        else:
                            # Pas d'executor, on ne peut pas exécuter le tool
                            tool_results.append({
                                'type': 'tool_result',
                                'tool_use_id': tool_use['id'],
                                'content': json.dumps({'error': 'Tool executor not available'}),
                                'is_error': True
                            })

                    # Ajouter les messages pour continuer la conversation
                    current_messages.append({
                        'role': 'assistant',
                        'content': response.content
                    })
                    current_messages.append({
                        'role': 'user',
                        'content': tool_results
                    })

        except anthropic.APIConnectionError as e:
            LogUtils.error(f"Erreur de connexion API Claude: {e}")
            yield {'type': 'error', 'error': 'Impossible de se connecter au service IA'}

        except anthropic.RateLimitError as e:
            LogUtils.error(f"Rate limit API Claude: {e}")
            yield {'type': 'error', 'error': 'Service temporairement surchargé, veuillez réessayer'}

        except anthropic.APIStatusError as e:
            LogUtils.error(f"Erreur API Claude: {e}")
            yield {'type': 'error', 'error': f'Erreur du service IA: {e.message}'}

        except Exception as e:
            LogUtils.error("Erreur inattendue lors de l'appel Claude")
            yield {'type': 'error', 'error': str(e)}

    def chat_completion(
        self,
        messages: List,
        page_context: Dict,
        user
    ) -> Dict[str, Any]:
        """
        Génère une réponse complète (non-streaming).

        Returns:
            Dict avec 'content', 'tokens_utilises', ou 'error'
        """
        try:
            # Extraire la question utilisateur
            user_question = ""
            if messages:
                last_msg = messages[-1] if hasattr(messages[-1], 'contenu') else messages[-1]
                user_question = getattr(last_msg, 'contenu', '') if hasattr(last_msg, 'contenu') else str(last_msg)

            system_prompt = self._build_system_prompt(page_context, user, user_question)

            # Utiliser l'optimisation des messages
            formatted_messages = self._optimize_messages(messages)

            if not formatted_messages:
                return {'error': 'Aucun message à traiter'}

            response = self.client.messages.create(
                model=self._model,
                max_tokens=self.MAX_TOKENS,
                system=system_prompt,
                messages=formatted_messages
            )

            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text

            total_tokens = 0
            if response.usage:
                total_tokens = response.usage.input_tokens + response.usage.output_tokens

            return {
                'content': content,
                'tokens_utilises': total_tokens,
                'input_tokens': response.usage.input_tokens if response.usage else 0,
                'output_tokens': response.usage.output_tokens if response.usage else 0
            }

        except Exception as e:
            LogUtils.error("Erreur lors de l'appel Claude")
            return {'error': str(e)}

    def analyze_code_for_bug(
        self,
        error_message: str,
        code_context: str,
        user_description: str
    ) -> Dict[str, Any]:
        """
        Analyse du code pour détecter un bug potentiel.

        Returns:
            Dict avec 'is_bug', 'analysis', 'recommendation'
        """
        prompt = f"""Analyse le problème suivant signalé par un utilisateur:

Description de l'utilisateur: {user_description}

Message d'erreur (si disponible): {error_message}

Code source pertinent:
```
{code_context}
```

Réponds au format JSON avec les clés suivantes:
- is_bug: boolean (true si c'est un bug dans le code, false si c'est une erreur utilisateur)
- analysis: string (explication du problème)
- recommendation: string (recommandation pour résoudre le problème)
- severity: string (low/medium/high si c'est un bug)
"""

        try:
            response = self.client.messages.create(
                model=self._model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text if response.content else "{}"

            # Essayer de parser le JSON
            try:
                # Extraire le JSON de la réponse
                import re
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

            return {
                'is_bug': False,
                'analysis': content,
                'recommendation': 'Contactez le support si le problème persiste.'
            }

        except Exception as e:
            LogUtils.error("Erreur lors de l'analyse de bug")
            return {
                'error': str(e),
                'is_bug': False,
                'analysis': 'Impossible d\'analyser le problème',
                'recommendation': 'Veuillez contacter le support technique.'
            }
