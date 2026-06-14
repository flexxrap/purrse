export function Logo({ size = 28, dark = false }) {
  const c = dark ? '#FF6B84' : '#E52B50'
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Left ear */}
      <path d="M23 43 L19 17 L44 34 Z" fill={c}/>
      {/* Right ear */}
      <path d="M77 43 L81 17 L56 34 Z" fill={c}/>

      {/* Body */}
      <ellipse cx="50" cy="64" rx="31" ry="27" fill={c}/>

      {/* Head */}
      <circle cx="50" cy="44" r="24" fill={c}/>

      {/* Tail */}
      <path d="M76 76 Q93 66 88 85" stroke={c} strokeWidth="9" strokeLinecap="round" fill="none"/>

      {/* Shine */}
      <path d="M67 33 Q80 45 75 60" stroke="rgba(255,255,255,0.22)" strokeWidth="5" strokeLinecap="round"/>

      {/* Paw bumps */}
      <ellipse cx="37" cy="88" rx="10" ry="6" fill={c}/>
      <ellipse cx="56" cy="90" rx="10" ry="6" fill={c}/>

      {/* Eyes */}
      <circle cx="41" cy="41" r="7" fill="white"/>
      <circle cx="59" cy="41" r="7" fill="white"/>

      {/* Nose */}
      <path d="M50 50 L47 55 L53 55 Z" fill="rgba(255,255,255,0.75)"/>
    </svg>
  )
}
