import { useEffect, useState } from 'react'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { FormItem, Form } from '@/components/ui/Form'
import { useAuth } from '@/auth'
import { useForm, Controller, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { CommonProps } from '@/@types/common'
import Radio from '@/components/ui/Radio'
import Select from '@/components/ui/Select'

interface SignUpFormProps extends CommonProps {
    disableSubmit?: boolean
    setMessage?: (message: string) => void
}

type SignUpFormSchema = {
    password: string
    email: string
    confirmPassword: string
    organizationMode: 'existing' | 'new'
    organizationSlug?: string
    organizationName?: string
    organizationDomain?: string
    role: 'owner' | 'admin' | 'member'
}

const validationSchema = z
    .object({
        email: z.email({ message: 'Please enter a valid email' }),
        password: z.string().min(1, { message: 'Password required' }),
        confirmPassword: z.string().min(1, { message: 'Confirm Password Required' }),
        organizationMode: z.enum(['existing', 'new']),
        organizationSlug: z.string().optional(),
        organizationName: z.string().optional(),
        organizationDomain: z.string().optional(),
        role: z.enum(['owner', 'admin', 'member']),
    })
    .refine((data) => data.password === data.confirmPassword, {
        message: 'Password not match',
        path: ['confirmPassword'],
    })
    .superRefine((data, ctx) => {
        if (data.organizationMode === 'existing' && !data.organizationSlug) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: 'Provide the organization ID you want to join',
                path: ['organizationSlug'],
            })
        }
        if (data.organizationMode === 'new' && !data.organizationName) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: 'Provide a name for the new organization',
                path: ['organizationName'],
            })
        }
    })

const roleOptions = [
    { value: 'owner', label: 'Owner' },
    { value: 'admin', label: 'Admin' },
    { value: 'member', label: 'Member' },
]

const SignUpForm = (props: SignUpFormProps) => {
    const { disableSubmit = false, className, setMessage } = props

    const [isSubmitting, setSubmitting] = useState<boolean>(false)

    const { signUp } = useAuth()

    const {
        handleSubmit,
        formState: { errors },
        control,
        setValue,
    } = useForm<SignUpFormSchema>({
        resolver: zodResolver(validationSchema),
        defaultValues: {
            organizationMode: 'new',
            role: 'owner',
        },
    })

    const organizationMode = useWatch({ control, name: 'organizationMode' })
    const selectedRole = useWatch({ control, name: 'role' })

    useEffect(() => {
        if (organizationMode === 'new') {
            setValue('role', 'owner', { shouldValidate: true })
            return
        }

        if (!['admin', 'member'].includes(selectedRole)) {
            setValue('role', 'member', { shouldValidate: true })
        }
    }, [organizationMode, selectedRole, setValue])

    const onSignUp = async (values: SignUpFormSchema) => {
        const {
            password,
            email,
            organizationMode: mode,
            organizationSlug,
            organizationName,
            organizationDomain,
            role,
        } = values

        if (!disableSubmit) {
            setSubmitting(true)
            const result = await signUp({
                userName: email,
                password,
                email,
                organizationMode: mode,
                organizationSlug: mode === 'existing' ? organizationSlug : undefined,
                organizationName: mode === 'new' ? organizationName : undefined,
                organizationDomain: mode === 'new' ? organizationDomain : undefined,
                role,
            })

            if (result?.status === 'failed') {
                setMessage?.(result.message)
            }

            setSubmitting(false)
        }
    }

    return (
        <div className={className}>
            <Form onSubmit={handleSubmit(onSignUp)}>
                <FormItem
                    label="Email"
                    invalid={Boolean(errors.email)}
                    errorMessage={errors.email?.message}
                >
                    <Controller
                        name="email"
                        control={control}
                        render={({ field }) => (
                            <Input
                                type="email"
                                placeholder="Email"
                                autoComplete="off"
                                {...field}
                            />
                        )}
                    />
                </FormItem>
                <FormItem
                    label="Organization"
                    invalid={Boolean(errors.organizationMode)}
                >
                    <Controller
                        name="organizationMode"
                        control={control}
                        render={({ field }) => (
                            <Radio.Group
                                value={field.value}
                                onChange={(value) => field.onChange(value)}
                                className="flex flex-col gap-2"
                            >
                                <Radio value="new">Create a new organization</Radio>
                                <Radio value="existing">Join an existing organization</Radio>
                            </Radio.Group>
                        )}
                    />
                </FormItem>
                {organizationMode === 'existing' && (
                    <FormItem
                        label="Organization ID"
                        invalid={Boolean(errors.organizationSlug)}
                        errorMessage={errors.organizationSlug?.message}
                    >
                        <Controller
                            name="organizationSlug"
                            control={control}
                            render={({ field }) => (
                                <Input
                                    type="text"
                                    placeholder="Enter the organization slug"
                                    autoComplete="off"
                                    {...field}
                                />
                            )}
                        />
                    </FormItem>
                )}
                {organizationMode === 'new' && (
                    <>
                        <FormItem
                            label="Organization name"
                            invalid={Boolean(errors.organizationName)}
                            errorMessage={errors.organizationName?.message}
                        >
                            <Controller
                                name="organizationName"
                                control={control}
                                render={({ field }) => (
                                    <Input
                                        type="text"
                                        placeholder="What should we call your workspace?"
                                        autoComplete="off"
                                        {...field}
                                    />
                                )}
                            />
                        </FormItem>
                        <FormItem
                            label="Organization domain (optional)"
                            invalid={Boolean(errors.organizationDomain)}
                            errorMessage={errors.organizationDomain?.message}
                        >
                            <Controller
                                name="organizationDomain"
                                control={control}
                                render={({ field }) => (
                                    <Input
                                        type="text"
                                        placeholder="e.g. irshad.com"
                                        autoComplete="off"
                                        {...field}
                                    />
                                )}
                            />
                        </FormItem>
                    </>
                )}
                <FormItem
                    label="Role"
                    invalid={Boolean(errors.role)}
                    errorMessage={errors.role?.message as string | undefined}
                >
                    <Controller
                        name="role"
                        control={control}
                        render={({ field }) => (
                            <Select
                                value={roleOptions.find((option) => option.value === field.value)}
                                options={
                                    organizationMode === 'existing'
                                        ? roleOptions.filter((option) => option.value !== 'owner')
                                        : roleOptions
                                }
                                isSearchable={false}
                                isDisabled={organizationMode === 'new'}
                                onChange={(option) => field.onChange(option?.value)}
                            />
                        )}
                    />
                </FormItem>
                <FormItem
                    label="Password"
                    invalid={Boolean(errors.password)}
                    errorMessage={errors.password?.message}
                >
                    <Controller
                        name="password"
                        control={control}
                        render={({ field }) => (
                            <Input
                                type="password"
                                autoComplete="off"
                                placeholder="Password"
                                {...field}
                            />
                        )}
                    />
                </FormItem>
                <FormItem
                    label="Confirm Password"
                    invalid={Boolean(errors.confirmPassword)}
                    errorMessage={errors.confirmPassword?.message}
                >
                    <Controller
                        name="confirmPassword"
                        control={control}
                        render={({ field }) => (
                            <Input
                                type="password"
                                autoComplete="off"
                                placeholder="Confirm Password"
                                {...field}
                            />
                        )}
                    />
                </FormItem>
                <Button
                    block
                    loading={isSubmitting}
                    variant="solid"
                    type="submit"
                >
                    {isSubmitting ? 'Creating Account...' : 'Sign Up'}
                </Button>
            </Form>
        </div>
    )
}

export default SignUpForm
