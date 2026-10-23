"""Original CoR teacher/student prompts, public feedback only, at most five repairs.

No model credential, hidden evaluator, TraceCoder, instrumentation or rollback.
The caller supplies public checker and transport; this module never executes code.
"""
import re
from intervenor import get_cor_prompt, get_repair_prompt


PUBLIC_FIELDS = {'problem_id', 'entry_point', 'prompt', 'tests', 'dataset', 'testtype'}


def extract(response, public):
    """Formatting adapter, not a syntax/correctness acceptance gate."""
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', response, re.S)
    if blocks:
        return blocks[0].strip('\n')
    # Original completion endpoint can return indented function bodies. Preserve
    # that supported form for HE; no AST rejection or automatic code repair.
    if public['dataset'] == 'humaneval' and response[:1].isspace():
        return public['prompt'] + '\n' + response
    return response.strip('\n')


def run(public, initial, generate, check, emit=lambda *args: None):
    if not set(public) <= PUBLIC_FIELDS or not public.get('tests'):
        raise ValueError('Expected public-only task with nonempty public tests')
    code = initial
    evaluation = check(code)
    emit('initial_public', {'evaluation': evaluation})
    history = []
    # The task and public examples accompany code for non-docstring datasets.
    # Comment representation prevents natural-language tasks becoming code.
    context = '# Public task and examples\n' + '\n'.join(
        '# ' + line for line in public['prompt'].splitlines())
    import json
    context += '\n# Public checks: ' + json.dumps(public['tests'], ensure_ascii=False)
    for turn in range(1, 6):
        if evaluation['passed']:
            break
        error = evaluation['result']
        buggy = context + '\n\n' + code + '\n'
        # Prompt functions and templates come directly from the official code.
        teacher = generate('teacher', turn, get_cor_prompt(buggy, error))
        # Keep the original function signature/docstring suffix for HE, and
        # public task comments for other interfaces (full program/class output).
        signature = public['prompt'] if public['dataset'] == 'humaneval' else context
        learner = generate('student', turn, get_repair_prompt(buggy, error, teacher, signature))
        code = extract(learner, public)
        evaluation = check(code)
        item = {'round': turn, 'teacher': teacher, 'student_response': learner,
                'code': code, 'public_evaluation': evaluation}
        history.append(item)
        emit('round', item)
    return {'problem_id': public['problem_id'], 'initial_code': initial,
            'final_code': code, 'final_public_evaluation': evaluation,
            'rounds': len(history), 'history': history, 'max_repairs': 5,
            'stop_reason': 'public_passed' if evaluation['passed'] else 'max_repairs',
            'hidden_used': False, 'method': 'INTERVENOR'}
