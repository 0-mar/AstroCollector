import {useForm} from "react-hook-form";
import {loginFormSchema, type LoginFormValues} from "@/features/auth/schemas.ts";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage} from "../../../components/ui/form.tsx";
import {Input} from "../../../components/ui/input.tsx";
import {Button} from "../../../components/ui/button.tsx";
import useLogin from "@/features/auth/useLogin.ts";
import {zodResolver} from "@hookform/resolvers/zod";

const LoginForm = () => {
    const loginMutation = useLogin()

    const form = useForm<LoginFormValues>({
        resolver: zodResolver(loginFormSchema),
        defaultValues: {
            email: "",
            password: ""
        },
    })

    const onSubmit = async (formData: LoginFormValues) => {
        await loginMutation.mutateAsync({email: formData.email, password: formData.password})
    }

    return (
        <div className={"w-auto md:w-1/2 mx-auto mt-4"}>
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
        </div>
    )
}

export default LoginForm
