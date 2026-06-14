export function Logo({ size = 28, dark = false }) {
  const color = dark ? '#FF6B84' : '#E52B50'
  const inner = dark ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.2)'
  return (
    <svg width={size} height={size} viewBox="0 0 38 38" fill="none">
      <path d="M4 11 L4 4 L14 11 Z" fill={color}/>
      <path d="M34 11 L34 4 L24 11 Z" fill={color}/>
      <path d="M5.5 10 L5.5 6 L12 10 Z" fill={inner}/>
      <path d="M32.5 10 L32.5 6 L26 10 Z" fill={inner}/>
      <rect x="3" y="10" width="32" height="25" rx="7" fill={color}/>
      <rect x="13" y="10" width="12" height="2.5" rx="1.25" fill="rgba(255,255,255,0.25)"/>
      <line x1="19" y1="17" x2="19" y2="30" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M15.5 20 C15.5 18 19 17.5 19 17.5 C22.5 17.5 22.5 20 22.5 21 C22.5 23.5 19 23.5 19 23.5 C15.5 23.5 15.5 26 15.5 27 C15.5 29 19 29.5 19 29.5 C22.5 29.5 22.5 27 22.5 27" stroke="white" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}
