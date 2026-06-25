import AppLayout from '../components/AppLayout'

// PLACEHOLDER — owned by Person B (Interactive Tutorial System, Feature 1).
// Routing (/tutorial in App.jsx) and the nav link (AppLayout.jsx) are already
// wired, so Person B only needs to replace the contents of this file and add
// any new components under src/components/. See PERSON_B_PROMPT.md.
function Tutorial() {
    return (
        <AppLayout>
            <section className="profile-header">
                <div>
                    <p className="eyebrow">Tutorial</p>
                    <h2>Interactive Tutorial — coming soon</h2>
                    <p>This page is being built. Module lessons and quizzes will appear here.</p>
                </div>
            </section>
        </AppLayout>
    )
}

export default Tutorial
