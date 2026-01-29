/**
 * Connect Dialog
 *
 * Modal for connecting to a bond.server instance.
 * Collects server URL and initial prompt.
 */

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"

interface ConnectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConnect: (serverUrl: string, prompt: string) => void
  isConnecting?: boolean
}

export function ConnectDialog({
  open,
  onOpenChange,
  onConnect,
  isConnecting = false,
}: ConnectDialogProps) {
  const [serverUrl, setServerUrl] = useState("http://localhost:8000")
  const [prompt, setPrompt] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (serverUrl && prompt) {
      onConnect(serverUrl, prompt)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Connect to Bond Server</DialogTitle>
            <DialogDescription>
              Enter your server URL and initial message to start a session.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 space-y-4">
            <div className="space-y-2">
              <label htmlFor="server-url" className="text-sm font-medium">
                Server URL
              </label>
              <Input
                id="server-url"
                placeholder="http://localhost:8000"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                disabled={isConnecting}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="prompt" className="text-sm font-medium">
                Message
              </label>
              <Input
                id="prompt"
                placeholder="Hello! What can you help me with?"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isConnecting}
                autoFocus
              />
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
              disabled={isConnecting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!serverUrl || !prompt || isConnecting}
            >
              {isConnecting ? "Connecting..." : "Connect"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
