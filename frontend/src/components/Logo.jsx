export function Logo({ size = 28 }) {
  return (
    <img
      src="/logo.svg"
      width={size}
      height={size}
      style={{ objectFit: 'contain' }}
      alt=""
    />
  )
}
