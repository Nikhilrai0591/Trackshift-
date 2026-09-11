import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null, info: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Surfaced on screen below AND logged, so it shows up in the browser
    // console even if someone doesn't scroll down to read the on-page box.
    console.error('TrackShift crashed:', error, info);
    this.setState({ info });
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          maxWidth: 760, margin: '80px auto', padding: 28, fontFamily: 'monospace',
          background: '#160406', border: '1px solid rgba(232,16,31,0.4)', borderRadius: 10, color: '#ffd3d6',
        }}>
          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 12, color: '#ff3b47' }}>
            TrackShift hit a render error (this box exists so you never just see a blank page):
          </div>
          <div style={{ fontSize: 13, whiteSpace: 'pre-wrap', marginBottom: 16 }}>
            {String(this.state.error?.message || this.state.error)}
          </div>
          {this.state.info?.componentStack && (
            <details style={{ fontSize: 11, opacity: 0.8 }}>
              <summary style={{ cursor: 'pointer', marginBottom: 8 }}>Component stack</summary>
              <pre style={{ whiteSpace: 'pre-wrap' }}>{this.state.info.componentStack}</pre>
            </details>
          )}
          <button
            onClick={() => window.location.reload()}
            style={{ marginTop: 16, padding: '8px 16px', background: '#e8101f', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' }}
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
