import { useEffect, useMemo, useState } from 'react'
import api from '../api/axios'
import AppLayout from '../components/AppLayout'
import TileCard, { makeTile } from '../components/TileCard'
import MeldDemo from '../components/MeldDemo'
import Quiz from '../components/Quiz'

// Lesson content for each module id (tiles, melds, winning-hands). The backend
// only stores completion and scores; the teaching content lives here.

const LESSON_CONTENT = {
    tiles: {
        lessons: [
            {
                title: 'The three numbered suits',
                body:
                    'Most of the wall is made of three suits numbered 1 to 9: Bamboo, Circles, and Characters. There are four copies of every tile.',
                tiles: [
                    makeTile('bamboo', 1),
                    makeTile('bamboo', 5),
                    makeTile('circles', 3),
                    makeTile('circles', 9),
                    makeTile('characters', 2),
                    makeTile('characters', 7),
                ],
            },
            {
                title: 'Honour tiles',
                body:
                    'Honour tiles have no number. The four winds are East, South, West, and North; the three dragons are Red, Green, and White.',
                tiles: [
                    makeTile('honour', 'east'),
                    makeTile('honour', 'south'),
                    makeTile('honour', 'west'),
                    makeTile('honour', 'north'),
                    makeTile('honour', 'red'),
                    makeTile('honour', 'green'),
                    makeTile('honour', 'white'),
                ],
            },
            {
                title: 'Bonus tiles: flowers and animals',
                body:
                    'Flowers and animals are bonus tiles unique to Singaporean Mahjong. They are set aside for points and immediately replaced, never forming part of your playing hand.',
                tiles: [
                    makeTile('flower', 'red_1'),
                    makeTile('flower', 'blue_1'),
                    makeTile('animal', 'cat'),
                    makeTile('animal', 'mouse'),
                ],
            },
        ],
        quiz: [
            {
                prompt: 'Which of these is an honour tile?',
                options: ['5 Bamboo', 'Green Dragon', '3 Circles', '9 Characters'],
                answer: 1,
            },
            {
                prompt: 'How many copies of each numbered tile are in the wall?',
                options: ['1', '2', '4', '9'],
                answer: 2,
            },
            {
                prompt: 'What happens to a flower or animal tile when you draw it?',
                options: [
                    'It stays in your hand as a normal tile',
                    'It is discarded immediately',
                    'It is set aside for bonus points and replaced',
                    'It ends the game',
                ],
                answer: 2,
            },
        ],
    },
    melds: {
        lessons: [
            {
                title: 'Pong — three identical tiles',
                meld: {
                    name: 'Pong',
                    tiles: [makeTile('circles', 5), makeTile('circles', 5), makeTile('circles', 5)],
                    description: 'Three of exactly the same tile.',
                },
            },
            {
                title: 'Kong — four identical tiles',
                meld: {
                    name: 'Kong',
                    tiles: [
                        makeTile('characters', 8),
                        makeTile('characters', 8),
                        makeTile('characters', 8),
                        makeTile('characters', 8),
                    ],
                    description: 'Four of the same tile. You draw a replacement after declaring it.',
                },
            },
            {
                title: 'Chow — a run of three',
                meld: {
                    name: 'Chow',
                    tiles: [makeTile('bamboo', 3), makeTile('bamboo', 4), makeTile('bamboo', 5)],
                    description: 'Three consecutive numbers in the same suit. Honours can never form a Chow.',
                },
            },
        ],
        quiz: [
            {
                prompt: 'A Pong is made of…',
                options: [
                    'Three consecutive tiles in a suit',
                    'Three identical tiles',
                    'Four identical tiles',
                    'A pair plus one',
                ],
                answer: 1,
            },
            {
                prompt: 'Which meld has four tiles?',
                options: ['Pong', 'Chow', 'Kong', 'Pair'],
                answer: 2,
            },
            {
                prompt: 'Which set is a valid Chow?',
                options: [
                    '3-4-5 Bamboo',
                    '5-5-5 Circles',
                    'East-South-West',
                    '2-4-6 Characters',
                ],
                answer: 0,
            },
        ],
    },
    'winning-hands': {
        lessons: [
            {
                title: 'The shape of a winning hand',
                body:
                    'A standard winning hand is four melds (Pongs, Kongs, or Chows) plus one pair — the "eyes". That is 14 tiles when you draw the winning tile.',
            },
            {
                title: 'A worked example',
                body:
                    'Here is a complete hand: a Chow, a Pong, a Chow, a Pong, and a pair of dragons.',
                groups: [
                    [makeTile('bamboo', 2), makeTile('bamboo', 3), makeTile('bamboo', 4)],
                    [makeTile('circles', 6), makeTile('circles', 6), makeTile('circles', 6)],
                    [makeTile('characters', 7), makeTile('characters', 8), makeTile('characters', 9)],
                    [makeTile('honour', 'east'), makeTile('honour', 'east'), makeTile('honour', 'east')],
                    [makeTile('honour', 'red'), makeTile('honour', 'red')],
                ],
            },
            {
                title: 'The pair',
                body:
                    'Every standard hand needs exactly one pair: two identical tiles. Without the pair you are not yet a winning hand, no matter how many melds you hold.',
                tiles: [makeTile('honour', 'red'), makeTile('honour', 'red')],
            },
        ],
        quiz: [
            {
                prompt: 'A standard winning hand is made of…',
                options: [
                    'Five melds',
                    'Four melds and a pair',
                    'Three Pongs and two Chows',
                    'Seven pairs only',
                ],
                answer: 1,
            },
            {
                prompt: 'How many tiles are in a complete standard hand (including the winning tile)?',
                options: ['13', '14', '16', '17'],
                answer: 1,
            },
            {
                prompt: 'What is the "pair" in a winning hand?',
                options: [
                    'Two consecutive tiles',
                    'Two identical tiles',
                    'Any two honour tiles',
                    'Two bonus tiles',
                ],
                answer: 1,
            },
        ],
    },
    'tai-scoring': {
        lessons: [
            {
                title: 'What is tai?',
                body:
                    'Tai are the points a winning hand is worth. A hand must be worth at least 1 tai before you are allowed to win. Tai come from special hand patterns, from winds and dragons, from being all one suit, and from bonus tiles. You add up every tai your hand qualifies for.',
            },
            {
                title: 'Winds and dragons',
                body:
                    'A Pong or Kong of a dragon (Red, Green, or White) scores 1 tai each. A Pong of your seat wind scores 1 tai, and a Pong of the round (prevailing) wind scores 1 tai — so if you are East in the East round, a Pong of East counts twice, for 2 tai. A single pair of winds or dragons scores nothing; you need the triplet.',
                groups: [
                    [makeTile('honour', 'red'), makeTile('honour', 'red'), makeTile('honour', 'red')],
                    [makeTile('honour', 'east'), makeTile('honour', 'east'), makeTile('honour', 'east')],
                ],
            },
            {
                title: 'Flushes and all pongs',
                body:
                    'A Half Flush — one suit plus honours — scores 2 tai. A Full Flush — one suit and no honours at all — scores 4 tai. All Pongs, a hand whose four sets are all Pongs or Kongs (no Chow), scores 2 tai. These stack with your wind and dragon tai.',
                groups: [
                    [makeTile('circles', 2), makeTile('circles', 3), makeTile('circles', 4)],
                    [makeTile('circles', 6), makeTile('circles', 7), makeTile('circles', 8)],
                    [makeTile('circles', 9), makeTile('circles', 9), makeTile('circles', 9)],
                    [makeTile('circles', 1), makeTile('circles', 1)],
                ],
            },
            {
                title: 'Pinghu',
                body:
                    'Pinghu is a hand of four Chows plus a pair with no flowers or animals — it scores 4 tai. If the same shape has any flower or animal it becomes a Smelly Pinghu, worth just 1 tai. Pinghu only counts on a self-draw, or on a discard where you were waiting on two possible tiles (for example holding 3-4 and able to win on 2 or 5).',
                groups: [
                    [makeTile('bamboo', 1), makeTile('bamboo', 2), makeTile('bamboo', 3)],
                    [makeTile('bamboo', 4), makeTile('bamboo', 5), makeTile('bamboo', 6)],
                    [makeTile('circles', 3), makeTile('circles', 4), makeTile('circles', 5)],
                    [makeTile('characters', 6), makeTile('characters', 7), makeTile('characters', 8)],
                    [makeTile('characters', 2), makeTile('characters', 2)],
                ],
            },
            {
                title: 'Special hands: Seven Pairs and Thirteen Orphans',
                body:
                    'Some hands break the usual four-melds-plus-a-pair shape. Seven Pairs — seven different pairs — scores 2 tai. Thirteen Orphans — one of every terminal (1 and 9 of each suit) and every honour, with one of them paired — is a hard, prized hand worth 5 tai.',
                tiles: [
                    makeTile('bamboo', 1), makeTile('bamboo', 9),
                    makeTile('circles', 1), makeTile('circles', 9),
                    makeTile('characters', 1), makeTile('characters', 9),
                    makeTile('honour', 'east'), makeTile('honour', 'south'),
                    makeTile('honour', 'west'), makeTile('honour', 'north'),
                    makeTile('honour', 'red'), makeTile('honour', 'green'),
                    makeTile('honour', 'white'),
                ],
            },
            {
                title: 'Flowers and animals',
                body:
                    'Bonus tiles score too. Each seat owns one flower number — East is 1, South is 2, West is 3, North is 4 — and holding your seat flower scores 1 tai. Every animal tile (cat, mouse, centipede, chicken) scores 1 tai. Flowers and animals count toward the 1-tai minimum, so a hand can win on its bonus tiles alone.',
                tiles: [
                    makeTile('flower', 'red_1'),
                    makeTile('animal', 'cat'),
                    makeTile('animal', 'mouse'),
                ],
            },
        ],
        quiz: [
            {
                prompt: 'How many tai must a hand be worth before you can win?',
                options: ['0', '1', '2', '5'],
                answer: 1,
            },
            {
                prompt: 'A Pong of the Green Dragon is worth…',
                options: ['0 tai', '1 tai', '2 tai', '4 tai'],
                answer: 1,
            },
            {
                prompt: 'A hand entirely in one suit with no honour tiles (Full Flush) scores…',
                options: ['1 tai', '2 tai', '4 tai', '5 tai'],
                answer: 2,
            },
            {
                prompt: 'Four Chows and a pair with no flowers or animals is called…',
                options: [
                    'All Pongs (2 tai)',
                    'Pinghu (4 tai)',
                    'Seven Pairs (2 tai)',
                    'Smelly Pinghu (1 tai)',
                ],
                answer: 1,
            },
            {
                prompt: 'Thirteen Orphans is worth how many tai?',
                options: ['2 tai', '3 tai', '4 tai', '5 tai'],
                answer: 3,
            },
            {
                prompt: 'Holding your own seat flower scores…',
                options: ['0 tai', '1 tai', '2 tai', 'It ends the game'],
                answer: 1,
            },
        ],
    },
}

function LessonView({ lesson }) {
    return (
        <div className="lesson-view">
            <h3>{lesson.title}</h3>
            {lesson.body && <p>{lesson.body}</p>}

            {lesson.meld && (
                <MeldDemo
                    name={lesson.meld.name}
                    tiles={lesson.meld.tiles}
                    description={lesson.meld.description}
                />
            )}

            {lesson.tiles && (
                <div className="tile-grid">
                    {lesson.tiles.map((tile, index) => (
                        <TileCard key={`${tile.code}-${index}`} tile={tile} />
                    ))}
                </div>
            )}

            {lesson.groups && (
                <div className="meld-group-row">
                    {lesson.groups.map((group, gi) => (
                        <div key={gi} className="meld-tile-row">
                            {group.map((tile, ti) => (
                                <TileCard key={`${tile.code}-${ti}`} tile={tile} />
                            ))}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

function Tutorial() {
    const [modules, setModules] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState('')

    const [activeId, setActiveId] = useState(null)
    const [step, setStep] = useState(0) // index into [lessons..., quiz]
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [saveError, setSaveError] = useState('')

    const fetchModules = async () => {
        try {
            const response = await api.get('/api/tutorial/modules/')
            setModules(response.data)
            setError('')
        } catch (err) {
            setError('Could not load tutorial modules. Please log in again and retry.')
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchModules()
    }, [])

    const activeModule = useMemo(
        () => modules.find((m) => m.id === activeId) || null,
        [modules, activeId]
    )
    const content = activeId ? LESSON_CONTENT[activeId] : null
    const lessons = content?.lessons || []
    const totalSteps = lessons.length + 1 // lessons + quiz step
    const completedCount = modules.filter((m) => m.completed).length

    const openModule = (id) => {
        setActiveId(id)
        setStep(0)
        setSaveError('')
    }

    const backToList = () => {
        setActiveId(null)
        setStep(0)
        setSaveError('')
    }

    const handleQuizComplete = async (score) => {
        setIsSubmitting(true)
        setSaveError('')
        try {
            await api.post('/api/tutorial/complete/', {
                module_id: activeId,
                quiz_score: score,
            })
            await fetchModules() // reflect saved completion from the server
        } catch (err) {
            setSaveError('Your score could not be saved. Please try again.')
        } finally {
            setIsSubmitting(false)
        }
    }

    // module list
    if (!activeId) {
        return (
            <AppLayout>
                <section className="profile-header">
                    <div>
                        <p className="eyebrow">Tutorial</p>
                        <h2>Interactive Tutorial</h2>
                        <p>
                            Work through short visual modules on tiles, melds, and winning
                            hands. Each module ends with a quick quiz, and your progress is
                            saved to your account.
                        </p>
                    </div>
                    <div className="hand-count">
                        <strong>{completedCount}/{modules.length}</strong>
                        <span>modules complete</span>
                    </div>
                </section>

                {error && <p className="error-message">{error}</p>}

                {isLoading ? (
                    <div className="empty-state">
                        <p>Loading modules…</p>
                    </div>
                ) : (
                    <section className="feature-grid" aria-label="Tutorial modules">
                        {modules.map((module) => (
                            <article key={module.id} className="feature-card module-card">
                                <div className="module-card-head">
                                    <h3>{module.title}</h3>
                                    {module.completed && (
                                        <span className="module-tick" aria-label="Completed">✓</span>
                                    )}
                                </div>
                                <p>{module.description}</p>
                                <div className="module-card-foot">
                                    {module.completed ? (
                                        <span className="module-status">
                                            Completed{module.quiz_score != null
                                                ? ` · score ${module.quiz_score}`
                                                : ''}
                                        </span>
                                    ) : (
                                        <span className="module-status">Not started</span>
                                    )}
                                    <button
                                        className="primary-button"
                                        type="button"
                                        onClick={() => openModule(module.id)}
                                    >
                                        {module.completed ? 'Review' : 'Start'}
                                    </button>
                                </div>
                            </article>
                        ))}
                    </section>
                )}
            </AppLayout>
        )
    }

    // module view
    if (!content) {
        return (
            <AppLayout>
                <section className="profile-header">
                    <div>
                        <p className="eyebrow">Tutorial</p>
                        <h2>{activeModule?.title || 'Module'}</h2>
                        <p>Lesson content for this module is coming soon.</p>
                    </div>
                    <button className="secondary-button" type="button" onClick={backToList}>
                        Back to modules
                    </button>
                </section>
            </AppLayout>
        )
    }

    const onQuizStep = step >= lessons.length
    const progressPct = Math.round((Math.min(step, totalSteps - 1) / (totalSteps - 1)) * 100)

    return (
        <AppLayout>
            <section className="profile-header">
                <div>
                    <p className="eyebrow">Tutorial · {activeModule?.title}</p>
                    <h2>{onQuizStep ? 'Module quiz' : lessons[step].title}</h2>
                    <p>
                        Step {Math.min(step + 1, totalSteps)} of {totalSteps}
                        {activeModule?.completed ? ' · already completed' : ''}
                    </p>
                </div>
                <button className="secondary-button" type="button" onClick={backToList}>
                    Back to modules
                </button>
            </section>

            <div className="tutorial-progress-bar" aria-hidden="true">
                <div
                    className="tutorial-progress-fill"
                    style={{ width: `${progressPct}%` }}
                />
            </div>

            <section className="panel">
                {onQuizStep ? (
                    <>
                        <Quiz
                            key={activeId}
                            questions={content.quiz}
                            onComplete={handleQuizComplete}
                            isSubmitting={isSubmitting}
                        />
                        {saveError && <p className="error-message">{saveError}</p>}
                        {activeModule?.completed && (
                            <div className="quiz-done-actions">
                                <button
                                    className="secondary-button"
                                    type="button"
                                    onClick={backToList}
                                >
                                    Done — back to modules
                                </button>
                            </div>
                        )}
                    </>
                ) : (
                    <>
                        <LessonView lesson={lessons[step]} />
                        <div className="lesson-nav">
                            <button
                                className="secondary-button"
                                type="button"
                                onClick={() => setStep((s) => Math.max(0, s - 1))}
                                disabled={step === 0}
                            >
                                Previous
                            </button>
                            <button
                                className="primary-button"
                                type="button"
                                onClick={() => setStep((s) => s + 1)}
                            >
                                {step === lessons.length - 1 ? 'Take the quiz' : 'Next'}
                            </button>
                        </div>
                    </>
                )}
            </section>
        </AppLayout>
    )
}

export default Tutorial
