// The MahjongSensei brand mark: a felt-green tile bearing 師 ("sensei").
// Rendered as styled DOM (see .logo-mark / .logo-lockup in index.css) so it
// stays crisp and inherits the design tokens.

export function LogoMark() {
    return (
        <span className="logo-mark" aria-hidden="true">
            師
        </span>
    )
}

// Mark + wordmark, used in the navbar and on the auth pages.
function Logo({ subtitle = 'Singapore Mahjong' }) {
    return (
        <span className="logo-lockup">
            <LogoMark />
            <span className="wordmark">
                MahjongSensei
                <small>{subtitle}</small>
            </span>
        </span>
    )
}

export default Logo
