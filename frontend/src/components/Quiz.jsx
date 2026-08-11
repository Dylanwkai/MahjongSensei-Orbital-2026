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

    // Once answered: highlight the right answer, flag a wrong pick, dim the rest.
    const optionClass = (index) => {
        if (!answered) return 'quiz-option'
        if (index === question.answer) return 'quiz-option quiz-correct'
        if (index === selected) return 'quiz-option quiz-wrong'
        return 'quiz-option quiz-dim'
    }

    return (
        <div className="quiz-panel">
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">Question {current + 1} of {questions.length}</p>
                    <h3>{question.prompt}</h3>
                </div>
            </div>

            <div className="quiz-options">
                {question.options.map((option, index) => (
                    <button
                        key={index}
                        type="button"
                        className={optionClass(index)}
                        onClick={() => choose(index)}
                        disabled={answered}
                    >
                        {option}
                    </button>
                ))}
            </div>

            {answered && (
                <div className="quiz-feedback">
                    <p>
                        {selected === question.answer
                            ? 'Correct!'
                            : `Not quite - the answer is "${question.options[question.answer]}".`}
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
