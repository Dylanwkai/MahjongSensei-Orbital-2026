import { useState } from 'react'

// A short multiple-choice quiz. `questions` is an array of:
//   { prompt, options: [string], answer: <index of correct option> }
// Calls onComplete(score, total) when the user finishes.
function Quiz({ questions, onComplete, isSubmitting }) {
    const [current, setCurrent] = useState(0)
    const [selected, setSelected] = useState(null)
    const [score, setScore] = useState(0)
    const [answered, setAnswered] = useState(false)
    const [finished, setFinished] = useState(false)

    const question = questions[current]
    const isLast = current === questions.length - 1

    const choose = (index) => {
        if (answered) return
        setSelected(index)
        setAnswered(true)
        if (index === question.answer) {
            setScore((s) => s + 1)
        }
    }

    const next = () => {
        const finalScore = score
        if (isLast) {
            setFinished(true)
            onComplete(finalScore, questions.length)
            return
        }
        setCurrent((c) => c + 1)
        setSelected(null)
        setAnswered(false)
    }

    if (finished) {
        return (
            <div className="quiz-panel">
                <p className="eyebrow">Quiz complete</p>
                <h3>You scored {score} / {questions.length}</h3>
                <p>{isSubmitting ? 'Saving your progress…' : 'Progress saved.'}</p>
            </div>
        )
    }

    const optionStyle = (index) => {
        const base = {
            textAlign: 'left',
            padding: '0.75rem 1rem',
            borderRadius: '10px',
            border: '1px solid rgba(148, 163, 184, 0.4)',
            background: 'rgba(255, 255, 255, 0.04)',
            color: 'inherit',
            cursor: answered ? 'default' : 'pointer',
            font: 'inherit',
        }
        if (!answered) return base
        if (index === question.answer) {
            return { ...base, borderColor: '#22c55e', background: 'rgba(34, 197, 94, 0.18)' }
        }
        if (index === selected) {
            return { ...base, borderColor: '#ef4444', background: 'rgba(239, 68, 68, 0.18)' }
        }
        return { ...base, opacity: 0.6 }
    }

    return (
        <div className="quiz-panel">
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">Question {current + 1} of {questions.length}</p>
                    <h3>{question.prompt}</h3>
                </div>
            </div>

            <div
                className="quiz-options"
                style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', margin: '1rem 0' }}
            >
                {question.options.map((option, index) => (
                    <button
                        key={index}
                        type="button"
                        className="quiz-option"
                        style={optionStyle(index)}
                        onClick={() => choose(index)}
                        disabled={answered}
                    >
                        {option}
                    </button>
                ))}
            </div>

            {answered && (
                <div className="quiz-feedback" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <p>
                        {selected === question.answer
                            ? 'Correct!'
                            : `Not quite — the answer is "${question.options[question.answer]}".`}
                    </p>
                    <button className="primary-button" type="button" onClick={next}>
                        {isLast ? 'Finish quiz' : 'Next question'}
                    </button>
                </div>
            )}
        </div>
    )
}

export default Quiz
