import os
import logging
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

_DIET_SYSTEM = """Você é um nutricionista especializado em evidências científicas.
Crie planos de dieta detalhados, práticos e seguros. Inclua sempre:
- Macros diários totais (proteína, carboidrato, gordura, calorias)
- Horários sugeridos de refeições
- Alimentos com quantidades em gramas
- Opções de substituição para cada refeição
Use linguagem clara, objetiva e motivadora. Formate com Markdown."""

_WORKOUT_SYSTEM = """Você é um personal trainer certificado baseado em evidências científicas.
Crie planos de treino detalhados, seguros e progressivos. Inclua sempre:
- Aquecimento e desaquecimento para cada dia
- Séries, repetições e tempo de descanso
- Dica de execução resumida por exercício
- Progressão sugerida para as primeiras 4 semanas
Use linguagem clara, objetiva e motivadora. Formate com Markdown."""

_CRITIC_SYSTEM = """Você é um revisor técnico severo de planos de saúde e fitness.
Sua única função é encontrar problemas. Você NUNCA aprova nada.
Analise e liste especificamente:
- Inconsistências entre o plano e o objetivo/perfil declarado
- Calorias, macros ou volume de treino inadequados para o peso/altura/nível
- Restrições alimentares não respeitadas
- Exercícios perigosos ou inadequados para o nível de condicionamento
- O que está faltando ou superestimado
Seja técnico e direto. Sem elogios."""


async def _call(system: str, prompt: str, max_tokens: int = 4096) -> str:
    msg = await _client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


async def generate_diet_plan(
    profile: dict,
    foods_context: list[dict],
    days: int,
    meals_per_day: int,
) -> str:
    foods_text = "\n".join(
        f"- {f['description']}: {f['calories']} kcal | {f['protein_g']}g prot | {f['carbs_g']}g carb | {f['fat_g']}g gord"
        for f in foods_context
    ) or "Sem dados externos — use seu conhecimento nutricional."

    profile_text = (
        f"Nome: {profile['name']} | Idade: {profile['age']} anos | "
        f"Peso: {profile['weight_kg']} kg | Altura: {profile['height_cm']} cm | "
        f"Objetivo: {profile['goal']} | "
        f"Restrições: {profile['dietary_restrictions'] or 'nenhuma'} | "
        f"Nível: {profile['fitness_level']} | Sexo: {profile.get('sex', 'masculino')}"
    )

    logger.info("diet step 1: draft")
    draft = await _call(_DIET_SYSTEM, f"""Crie um plano de dieta de {days} dias com {meals_per_day} refeições/dia para:
{profile_text}

Referências nutricionais (USDA):
{foods_text}

Organize por dia. Inclua totais de macros ao final de cada dia.""")

    logger.info("diet step 2: critique")
    critique = await _call(_CRITIC_SYSTEM, f"""Perfil do usuário: {profile_text}

Referências nutricionais (USDA):
{foods_text}

Plano de dieta gerado:
{draft}

Liste todos os problemas deste plano.""", max_tokens=1024)

    logger.info("diet step 3: refinement")
    final = await _call(_DIET_SYSTEM, f"""Você gerou um plano de dieta que foi criticado por um revisor.
Reescreva o plano corrigindo TODOS os problemas apontados.

Perfil: {profile_text}

Referências nutricionais (USDA):
{foods_text}

Plano original:
{draft}

Problemas a corrigir:
{critique}

Entregue apenas o plano final corrigido, sem mencionar o processo de revisão.""")

    return final


async def generate_workout_plan(
    profile: dict,
    exercises_context: list[dict],
    days_per_week: int,
    focus: str,
) -> str:
    exercises_text = "\n".join(
        f"- {e['name']} | parte: {e['bodyPart']} | alvo: {e['target']} | equip: {e['equipment']}"
        for e in exercises_context
    ) or "Sem dados externos — use seu conhecimento de exercícios."

    profile_text = (
        f"Nome: {profile['name']} | Idade: {profile['age']} anos | "
        f"Peso: {profile['weight_kg']} kg | Altura: {profile['height_cm']} cm | "
        f"Objetivo: {profile['goal']} | Nível: {profile['fitness_level']}"
    )

    logger.info("workout step 1: draft")
    draft = await _call(_WORKOUT_SYSTEM, f"""Crie um plano de treino de {days_per_week} dias/semana com foco em {focus} para:
{profile_text}

Exercícios disponíveis (ExerciseDB):
{exercises_text}

Organize por dia de treino (ex: Dia A, Dia B...). Inclua aquecimento e desaquecimento.""")

    logger.info("workout step 2: critique")
    critique = await _call(_CRITIC_SYSTEM, f"""Perfil do usuário: {profile_text}
Foco do treino: {focus}

Exercícios disponíveis (ExerciseDB):
{exercises_text}

Plano de treino gerado:
{draft}

Liste todos os problemas deste plano.""", max_tokens=1024)

    logger.info("workout step 3: refinement")
    final = await _call(_WORKOUT_SYSTEM, f"""Você gerou um plano de treino que foi criticado por um revisor.
Reescreva o plano corrigindo TODOS os problemas apontados.

Perfil: {profile_text}
Foco: {focus}

Exercícios disponíveis (ExerciseDB):
{exercises_text}

Plano original:
{draft}

Problemas a corrigir:
{critique}

Entregue apenas o plano final corrigido, sem mencionar o processo de revisão.""")

    return final
