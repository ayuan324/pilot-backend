"use client"
import { useEffect, useState } from "react"

interface Star {
  id: number
  x: number
  y: number
  size: number
  color: string
  speedX: number
  speedY: number
  opacity: number
}

export default function StarryBackground() {
  const [stars, setStars] = useState<Star[]>([])

  useEffect(() => {
    const colors = ['#60a5fa', '#a78bfa', '#34d399', '#f472b6', '#fbbf24', '#06b6d4']

    // Create initial stars
    const initialStars: Star[] = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: Math.random() * 3 + 1,
      color: colors[Math.floor(Math.random() * colors.length)],
      speedX: (Math.random() - 0.5) * 1.2,
      speedY: (Math.random() - 0.5) * 1.2,
      opacity: Math.random() * 0.8 + 0.2
    }))

    setStars(initialStars)

    // Animation loop
    const animate = () => {
      setStars(prev => prev.map(star => {
        let newX = star.x + star.speedX
        let newY = star.y + star.speedY

        // Wrap around edges
        if (newX < 0) newX = window.innerWidth
        if (newX > window.innerWidth) newX = 0
        if (newY < 0) newY = window.innerHeight
        if (newY > window.innerHeight) newY = 0

        return {
          ...star,
          x: newX,
          y: newY
        }
      }))
    }

    const interval = setInterval(animate, 30)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {stars.map(star => (
        <div
          key={star.id}
          className="absolute rounded-full animate-pulse"
          style={{
            left: `${star.x}px`,
            top: `${star.y}px`,
            width: `${star.size}px`,
            height: `${star.size}px`,
            backgroundColor: star.color,
            opacity: star.opacity,
            boxShadow: `0 0 ${star.size * 2}px ${star.color}`,
            transition: 'all 0.05s ease-out'
          }}
        />
      ))}
    </div>
  )
}
