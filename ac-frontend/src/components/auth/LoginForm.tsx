import {useForm} from "react-hook-form";
import {yupResolver} from "@hookform/resolvers/yup";
import {loginFormSchema, type LoginValues} from "@/features/auth/schemas.ts";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage} from "../../../components/ui/form.tsx";
import {Input} from "../../../components/ui/input.tsx";
import {type Tokens} from "@/features/auth/useAuth.ts";
import {Button} from "../../../components/ui/button.tsx";
import {useMutation} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import {toast} from "sonner";
import {useContext} from "react";
import {AuthContext, type User} from "@/components/auth/AuthContext.tsx";
import {setHeaderToken} from "@/features/api/refresh.ts";

const LoginForm = () => {
    const authContext = useContext(AuthContext)

    const form = useForm<LoginValues>({
        resolver: yupResolver(loginFormSchema),
        defaultValues: {
            email: "",
            password: ""
        },
    })

    //const [accessToken, loginMutation] = useAuth()

    const loginMutation = useMutation({
        mutationFn: ({email, password}: {email: string, password: string}) => {
            const params = new URLSearchParams();
            params.append("username", email);
            params.append("password", password);
            return BaseApi.post<Tokens>(`/security/login`, params, { headers: { "Content-Type": "application/x-www-form-urlencoded" } })
        },
        onError: (_error) => {
            toast.error("Login failed")
        },
        onSuccess: (data) => {
            authContext?.setAccessToken(data.access_token)
            setHeaderToken(data.access_token)
            console.log(data)
        },
    });

    const onSubmit = async (formData: LoginValues) => {
        await loginMutation.mutateAsync({email: formData.email, password: formData.password})
    }

    const userMutation = useMutation({
        mutationFn: () => {
            return BaseApi.get<User>("/security/me")
        },
        onError: (_error) => {
            toast.error("Login failed")
        },
        onSuccess: (data) => {
            console.log(data)
        },
    });

    return (
        <>
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                    control={form.control}
                    name="email"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Email</FormLabel>
                            <FormControl>
                                <Input type="email" placeholder="example@example.com" {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="password"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Password</FormLabel>
                            <FormControl>
                                <Input type="password" {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <Button type="submit">Log in</Button>
            </form>
        </Form>
            <Button onClick={() => userMutation.mutateAsync()
            }>Get Info</Button>
        </>
    )
}

export default LoginForm
