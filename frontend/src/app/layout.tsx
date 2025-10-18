import 'bootstrap/dist/css/bootstrap.min.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <header>
          <nav className="navbar navbar-expand-lg navbar-light bg-light">
            <div className="container-fluid">
              <a className="navbar-brand" href="#">Online Doc</a>
            </div>
          </nav>
        </header>
        <main className="container mt-4">
          {children}
        </main>
      </body>
    </html>
  )
}
