"use client"

import type React from "react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { CheckCircle, Upload, XCircle } from "lucide-react"
import { useState } from "react"

interface ApiResponse {
    status: "success" | "error"
    score?: number
    total_questions?: number
    message?: string
}

export default function GradingPlatform() {
    const [image, setImage] = useState<File | null>(null)
    const [answers, setAnswers] = useState("")
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<ApiResponse | null>(null)

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setImage(e.target.files[0])
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!image || !answers.trim()) {
            setResult({
                status: "error",
                message: "Please provide both an image and answers",
            })
            return
        }

        // Process answers into array format
        function convertToIndexedObject(str: string): { [key: number]: number } {
            const arr = str.split(','); // Split the string into an array
            const result: { [key: number]: number } = {};

            arr.forEach((value, index) => {
                result[Number(index)] = Number(value); // Convert each value to a number
            });

            return result;
        }

        setLoading(true)
        setResult(null)

        try {
            const formData = new FormData()
            formData.append("omr", image)
            formData.append("answers", answers)

            const response = await fetch(process.env.NEXT_PUBLIC_API_URL!, {
                method: "POST",
                body: formData,
            })

            const data: ApiResponse = await response.json()
            setResult(data)
        } catch (error) {
            setResult({
                status: "error",
                message: "Failed to connect to server",
            })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-background p-4">
            <div className="max-w-md mx-auto space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="text-center">Grading Platform</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {/* Image Upload */}
                            <div className="space-y-2">
                                <Label htmlFor="image">Upload Image</Label>
                                <div className="border-2 border-dashed border-border rounded-lg p-4 text-center">
                                    <Input id="image" type="file" accept="image/*" onChange={handleImageChange} className="hidden" />
                                    <Label htmlFor="image" className="cursor-pointer flex flex-col items-center gap-2">
                                        <Upload className="h-8 w-8 text-muted-foreground" />
                                        <span className="text-sm text-muted-foreground">
                                            {image ? image.name : "Click to upload image"}
                                        </span>
                                    </Label>
                                </div>
                            </div>

                            {/* Answers Input */}
                            <div className="space-y-2">
                                <Label htmlFor="answers">Answers (1-4, separated by commas)</Label>
                                <Textarea
                                    id="answers"
                                    placeholder="1,3,4,3,2"
                                    value={answers}
                                    onChange={(e) => setAnswers(e.target.value)}
                                    className="min-h-[80px]"
                                />
                                <p className="text-xs text-muted-foreground">Enter answers between 1-4, separated by commas</p>
                            </div>

                            <Button type="submit" disabled={loading} className="w-full">
                                {loading ? "Processing..." : "Submit"}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                {/* Results */}
                {
                    result && (
                        <Card>
                            <CardContent className="pt-6">
                                {
                                    result.status === "success" ? (
                                        <div className="text-center space-y-4">
                                            <div className="flex items-center justify-center gap-2 text-green-600">
                                                <CheckCircle className="h-6 w-6" />
                                                <span className="font-semibold">Success!</span>
                                            </div>
                                            <div className="space-y-2">
                                                <div className="text-3xl font-bold text-primary">
                                                    {result.score}/{result.total_questions}
                                                </div>
                                                <div className="text-sm text-muted-foreground">
                                                    Score: {Math.round((result.score! / result.total_questions!) * 100)}%
                                                </div>
                                                <div className="w-full bg-secondary rounded-full h-2">
                                                    <div
                                                        className="bg-primary h-2 rounded-full transition-all duration-500"
                                                        style={{
                                                            width: `${(result.score! / result.total_questions!) * 100}%`,
                                                        }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <Alert variant="destructive">
                                            <XCircle className="h-4 w-4" />
                                            <AlertDescription className="flex items-center gap-2">
                                                <span className="font-semibold">Error:</span>
                                                {result.message}
                                            </AlertDescription>
                                        </Alert>
                                    )
                                }
                            </CardContent>
                        </Card>
                    )
                }
            </div>
        </div>
    )
}
